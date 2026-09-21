import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { cancelRequest, requestExplicitReview, sendChatMessage } from "../api/endpoints";
import ConfirmDialog from "../components/ConfirmDialog";
import StatusPill from "../components/StatusPill";
import type { AccessRequest, ChatMessage } from "../types";

interface Turn {
  message: ChatMessage;
  createdRequests?: AccessRequest[];
}

const TAKE_BACKABLE_STATUSES = new Set(["pending", "escalated", "pending_client_approval"]);

function AssistantText({ text, animate }: { text: string; animate: boolean }) {
  const [display, setDisplay] = useState(animate ? "" : text);

  useEffect(() => {
    if (!animate) return;
    let i = 0;
    const step = Math.max(1, Math.ceil(text.length / 90));
    const interval = setInterval(() => {
      i += step;
      setDisplay(text.slice(0, i));
      if (i >= text.length) clearInterval(interval);
    }, 16);
    return () => clearInterval(interval);
    
  }, []);

  return <div className="chat-bubble-content">{display}</div>;
}

export default function Chat() {
  const [applicationId, setApplicationId] = useState<string | null>(null);
  const [applicationName, setApplicationName] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewRequested, setReviewRequested] = useState<Record<string, boolean>>({});
  const [takeBackTarget, setTakeBackTarget] = useState<AccessRequest | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || isSending) return;
    setError(null);

    const userTurn: Turn = { message: { role: "user", content: input.trim() } };
    const history = [...turns.map((t) => t.message), userTurn.message];
    setTurns((prev) => [...prev, userTurn]);
    setInput("");
    setIsSending(true);

    try {
      const result = await sendChatMessage(applicationId, history);
      if (result.resolved_application_id) {
        setApplicationId(result.resolved_application_id);
        setApplicationName(result.resolved_application_name);
      }
      setTurns((prev) => [...prev, { message: { role: "assistant", content: result.reply }, createdRequests: result.created_requests }]);
    } catch {
      setError("The assistant didn't respond. Try again.");
    } finally {
      setIsSending(false);
    }
  }

  function changeApplication() {
    setApplicationId(null);
    setApplicationName(null);
    setTurns([]);
  }

  async function handleRequestReview(requestId: string) {
    setReviewRequested((prev) => ({ ...prev, [requestId]: true }));
    try {
      const updated = await requestExplicitReview(requestId);
      setTurns((prev) =>
        prev.map((t) => ({
          ...t,
          createdRequests: t.createdRequests?.map((r) => (r.id === requestId ? updated : r)),
        }))
      );
    } catch {
      setReviewRequested((prev) => ({ ...prev, [requestId]: false }));
    }
  }

  async function confirmTakeBack() {
    if (!takeBackTarget) return;
    try {
      const updated = await cancelRequest(takeBackTarget.id);
      setTurns((prev) =>
        prev.map((t) => ({
          ...t,
          createdRequests: t.createdRequests?.map((r) => (r.id === takeBackTarget.id ? updated : r)),
        }))
      );
      setTakeBackTarget(null);
    } catch {
      setTakeBackTarget(null);
    }
  }

  const lastAssistantIndex = (() => {
    for (let i = turns.length - 1; i >= 0; i--) {
      if (turns[i].message.role === "assistant") return i;
    }
    return -1;
  })();

  return (
    <div className="chat-page">
      <div className="chat-toolbar">
        {applicationName ? (
          <span className="chat-app-chip">
            {applicationName}
            <button type="button" className="chat-app-chip-clear" onClick={changeApplication}>
              Change
            </button>
          </span>
        ) : (
          <span className="hint-text">Mention the application in your message — e.g. "billing service".</span>
        )}
      </div>

      <div className="chat-transcript">
        {turns.length === 0 && (
          <p className="chat-empty-hint">
            Describe the access you need, e.g. "I need read access to the billing service repo" — I'll figure out
            which application you mean, then check your ADO tasks, the catalog, and any uploaded docs before
            proposing anything.
          </p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className={`chat-bubble ${turn.message.role}`}>
            {turn.message.role === "assistant" ? (
              <AssistantText text={turn.message.content} animate={i === lastAssistantIndex} />
            ) : (
              <div className="chat-bubble-content">{turn.message.content}</div>
            )}
            {turn.createdRequests && turn.createdRequests.length > 0 && (
              <div className="chat-request-cards">
                {turn.createdRequests.map((r) => (
                  <div key={r.id} className="chat-request-card">
                    <div className="chat-request-card-top">
                      <StatusPill status={r.status} />
                      {r.severity && <span className="severity-tag">{r.severity}</span>}
                    </div>
                    <p>{r.requested_text}</p>
                    <div className="chat-request-card-actions">
                      {r.status === "cannot_verify" && (
                        <button
                          className="secondary-button chat-review-button"
                          disabled={reviewRequested[r.id]}
                          onClick={() => handleRequestReview(r.id)}
                        >
                          {reviewRequested[r.id] ? "Sent to your manager" : "Request explicit review"}
                        </button>
                      )}
                      {TAKE_BACKABLE_STATUSES.has(r.status) && (
                        <button className="secondary-button chat-review-button" onClick={() => setTakeBackTarget(r)}>
                          Take back
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {isSending && (
          <div className="chat-bubble assistant chat-thinking">
            <span className="thinking-dot" />
            <span className="thinking-dot" />
            <span className="thinking-dot" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="error">{error}</p>}

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          placeholder="Describe the access you need..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isSending}
          autoFocus
        />
        <button type="submit" disabled={isSending || !input.trim()}>
          Send
        </button>
      </form>

      <ConfirmDialog
        open={takeBackTarget !== null}
        title="Take back this request?"
        message={`"${takeBackTarget?.requested_text}" will be withdrawn. You can always ask again later.`}
        confirmLabel="Take back"
        onConfirm={confirmTakeBack}
        onCancel={() => setTakeBackTarget(null)}
      />
    </div>
  );
}
