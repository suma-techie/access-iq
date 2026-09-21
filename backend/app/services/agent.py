
import json
import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.user import User
from app.services.catalog_search import search_catalog
from app.services.doc_search import search_docs
from app.services.integrations.ado import get_ado_tasks
from app.services.llm import LLMError, chat_completion
from app.services.routing import (
    OutOfScopeOutcome,
    ProposalOutcome,
    apply_out_of_scope_outcome,
    apply_proposal_outcome,
    create_cannot_verify_request,
)
from app.services.text_match import score_overlap, tokenize

MAX_ITERATIONS = 6

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Alias/rule match against this application's permission catalog. Always call this first for any specific permission ask.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The permission being asked for, in plain words."}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ado_tasks",
            "description": "Get the requesting user's current/recent Azure DevOps work items, to check if one justifies this access ask.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_doc",
            "description": "Search this application's lead/owner-uploaded documentation for text that justifies this access ask.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "What to search for in the documentation."}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_permission",
            "description": (
                "Bind one specific, distinct permission ask to a grounded permission_id you found via search_catalog. "
                "Only call this after calling search_catalog (and, if that match wasn't a strong/exact one, also "
                "get_ado_tasks and get_doc to look for corroborating evidence). Call once per distinct permission ask."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "requested_text": {"type": "string", "description": "The specific ask this proposal addresses, in the user's words."},
                    "permission_id": {"type": "string", "description": "The permission_id from a search_catalog result."},
                    "source_type": {
                        "type": "string",
                        "enum": ["catalog_exact", "ado_task", "doc"],
                        "description": "catalog_exact if search_catalog's match alone was strong/exact; ado_task or doc if you needed that evidence to justify a weaker catalog match.",
                    },
                    "source_ref": {
                        "type": "object",
                        "description": "For ado_task: {\"ado_task_id\": ...}. For doc: {\"doc_id\": ...}. For catalog_exact: {}.",
                    },
                    "rationale": {"type": "string", "description": "One sentence: why this is grounded."},
                },
                "required": ["requested_text", "permission_id", "source_type", "source_ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_unverifiable",
            "description": (
                "Call this for a specific, nameable permission ask that you identified but could NOT find in the "
                "catalog at all (search_catalog returned nothing usable), even after checking ADO tasks and docs. "
                "This routes it to manager review instead of silently dropping it. Do not use this for vague asks "
                "you can't even name — just say so in your reply instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "requested_text": {"type": "string"},
                    "note": {"type": "string", "description": "Why nothing could be found."},
                },
                "required": ["requested_text"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are AccessIQ's access-request assistant for the application "{application_name}".

Your only job: turn the user's message into one or more grounded permission proposals, or ask a clarifying
question if you don't yet know which application/permission they mean.

Rules (mandatory, no exceptions):
1. Never claim a permission is justified from your own knowledge. Every proposal must trace to a tool result.
2. For each distinct permission ask in the message: call search_catalog first. If it returns a strong/exact
   match, call propose_permission with source_type="catalog_exact" right away (no need to also check ADO/docs).
3. If search_catalog's match is weak, or empty, call get_ado_tasks and get_doc to look for corroborating
   evidence before deciding. Use whichever evidence is stronger as the source_type on propose_permission.
4. If search_catalog returns nothing at all for a specific, nameable ask (even after checking ADO/docs), call
   flag_unverifiable for it instead of propose_permission. Never invent a permission_id.
5. If the message is too vague to identify any specific permission (e.g. small talk, or "I need more access"
   with no specifics), just ask a clarifying question in plain text and do not call any tools yet.
6. If the message asks for several distinct things, handle each independently — some may be grounded, some
   may not; that's expected and fine.
7. Once you've called propose_permission/flag_unverifiable for everything you can identify in the message,
   reply with a short, plain-English summary of what you did. Do not call the same tool redundantly.
"""


@dataclass
class _ToolState:
    catalog_confidence: dict[str, float] = field(default_factory=dict)
    ado_tasks: dict[str, str] = field(default_factory=dict)
    doc_confidence: dict[str, float] = field(default_factory=dict)
    searched_anything: bool = False


@dataclass
class AgentResult:
    reply: str
    created_requests: list


def _tool_error(message: str) -> dict:
    return {"error": message}


def _execute_search_catalog(db: Session, application: Application, args: dict, state: _ToolState) -> dict:
    query = args.get("query", "")
    matches = search_catalog(db, application.id, query)
    for m in matches:
        state.catalog_confidence[str(m.catalog_entry_id)] = max(state.catalog_confidence.get(str(m.catalog_entry_id), 0.0), m.confidence)
    if not matches:
        return {"matches": []}
    return {
        "matches": [
            {
                "permission_id": str(m.catalog_entry_id),
                "permission_name": m.permission_name,
                "severity": m.severity,
                "confidence": m.confidence,
            }
            for m in matches
        ]
    }


def _execute_get_ado_tasks(requester: User, state: _ToolState) -> dict:
    try:
        tasks = get_ado_tasks(requester)
    except NotImplementedError:
        return {"tasks": []}
    for t in tasks:
        state.ado_tasks[t.task_id] = f"{t.title}. {t.description}"
    return {"tasks": [{"task_id": t.task_id, "title": t.title, "description": t.description, "project": t.project, "status": t.status} for t in tasks]}


def _execute_get_doc(db: Session, application: Application, args: dict, state: _ToolState) -> dict:
    query = args.get("query", "")
    matches = search_docs(db, application.id, query)
    for m in matches:
        state.doc_confidence[str(m.doc_id)] = max(state.doc_confidence.get(str(m.doc_id), 0.0), m.confidence)
    if not matches:
        return {"matches": []}
    return {
        "matches": [
            {"doc_id": str(m.doc_id), "filename": m.filename, "excerpt": m.chunk_text, "confidence": m.confidence}
            for m in matches
        ]
    }


def _execute_propose_permission(args: dict, state: _ToolState, outcomes: list) -> dict:
    requested_text = args.get("requested_text", "").strip()
    permission_id = args.get("permission_id", "")
    source_type = args.get("source_type", "")
    source_ref = args.get("source_ref") or {}
    rationale = args.get("rationale")

    if not requested_text or not permission_id or source_type not in ("catalog_exact", "ado_task", "doc"):
        return _tool_error("Missing or invalid requested_text/permission_id/source_type.")

    if permission_id not in state.catalog_confidence:
        return _tool_error(
            f"permission_id {permission_id} was never returned by search_catalog this turn. Call search_catalog first."
        )

    try:
        entry_uuid = uuid.UUID(permission_id)
    except ValueError:
        return _tool_error("permission_id must be a UUID from a search_catalog result.")

    if source_type == "catalog_exact":
        confidence = state.catalog_confidence[permission_id]
    elif source_type == "ado_task":
        task_id = source_ref.get("ado_task_id")
        task_text = state.ado_tasks.get(task_id)
        if task_text is None:
            return _tool_error(f"ado_task_id {task_id!r} was never returned by get_ado_tasks this turn. Call get_ado_tasks first.")
        confidence = score_overlap(tokenize(requested_text), task_text)
    else:
        doc_id = source_ref.get("doc_id")
        if doc_id not in state.doc_confidence:
            return _tool_error(f"doc_id {doc_id!r} was never returned by get_doc this turn. Call get_doc first.")
        confidence = state.doc_confidence[doc_id]

    outcomes.append(
        ProposalOutcome(
            requested_text=requested_text,
            catalog_entry_id=entry_uuid,
            source_type=source_type,
            source_reference=source_ref,
            confidence=confidence,
            ai_rationale=rationale,
        )
    )
    return {"accepted": True, "confidence": round(confidence, 3)}


def _execute_flag_unverifiable(args: dict, outcomes: list) -> dict:
    requested_text = args.get("requested_text", "").strip()
    if not requested_text:
        return _tool_error("requested_text is required.")
    outcomes.append(OutOfScopeOutcome(requested_text=requested_text, ai_rationale=args.get("note")))
    return {"accepted": True}


def run_agent(db: Session, requester: User, application: Application, history: list[dict]) -> AgentResult:
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT.format(application_name=application.name)}
    ] + history

    state = _ToolState()
    outcomes: list = []
    last_message: dict = {"content": ""}

    for _ in range(MAX_ITERATIONS):
        try:
            last_message = chat_completion(messages, tools=TOOLS)
        except LLMError as exc:
            return AgentResult(reply=f"I couldn't reach the language model: {exc}", created_requests=[])

        messages.append(last_message)
        tool_calls = last_message.get("tool_calls")
        if not tool_calls:
            break

        for tool_call in tool_calls:
            fn = tool_call["function"]["name"]
            try:
                args = json.loads(tool_call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}

            if fn == "search_catalog":
                state.searched_anything = True
                result = _execute_search_catalog(db, application, args, state)
            elif fn == "get_ado_tasks":
                state.searched_anything = True
                result = _execute_get_ado_tasks(requester, state)
            elif fn == "get_doc":
                state.searched_anything = True
                result = _execute_get_doc(db, application, args, state)
            elif fn == "propose_permission":
                result = _execute_propose_permission(args, state, outcomes)
            elif fn == "flag_unverifiable":
                result = _execute_flag_unverifiable(args, outcomes)
            else:
                result = _tool_error(f"Unknown tool {fn!r}")

            messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": json.dumps(result)})

    reply = last_message.get("content") or "I've processed your request."

    created_requests = []
    if outcomes:
        for outcome in outcomes:
            if isinstance(outcome, ProposalOutcome):
                created_requests.append(apply_proposal_outcome(db, requester, application, outcome))
            else:
                created_requests.append(apply_out_of_scope_outcome(db, requester, application, outcome))
    elif state.searched_anything:
        last_user_message = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        created_requests.append(create_cannot_verify_request(db, requester, application, last_user_message))
        reply = (
            "I couldn't find this in your assigned ADO tasks or your application's documentation. "
            "Please ask your Team Lead / Application Owner to confirm this need, or upload/update the relevant documentation."
        )

    return AgentResult(reply=reply, created_requests=created_requests)
