
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()


class LLMError(RuntimeError):
    pass


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    temperature: float | None = None,
) -> dict[str, Any]:
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    body: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
    }
    if temperature is not None:
        body["temperature"] = temperature
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    try:
        response = httpx.post(url, headers=headers, json=body, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise LLMError(f"LLM endpoint returned {exc.response.status_code}: {exc.response.text[:500]}") from exc
    except httpx.HTTPError as exc:
        raise LLMError(f"LLM endpoint request failed: {exc}") from exc

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise LLMError(f"LLM response had no choices: {data}")
    return choices[0]["message"]
