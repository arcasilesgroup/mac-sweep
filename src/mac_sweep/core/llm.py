"""Multi-provider LLM agent for mac-sweep.

Supports Claude (Anthropic) and GPT (OpenAI) APIs using only Python
stdlib (urllib). No pip dependencies required.

Core module: raises LLMError instead of printing to stderr.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from mac_sweep.core.config import LLM_TIMEOUT, load_config
from mac_sweep.core.errors import LLMError
from mac_sweep.core.models import CleanupCandidate

SYSTEM_PROMPT = """You are a macOS cleanup assistant that helps users remove unused software.
You understand commands in English and Spanish.

Given the list of installed software below and the user's request,
select which items should be removed.

IMPORTANT RULES:
- Only select items from the PROVIDED LIST below. Never invent items.
- Never select Apple system apps (Safari, Mail, Finder, Terminal, etc.)
- Never select items that are dependencies of other packages.
- If the user's request is vague (e.g., "clean up old stuff"), prefer
  items with Dormant status over Active or Occasional.
- If the user asks what they can remove, list all Dormant candidates.

Respond ONLY with valid JSON in this exact format:
{{"items": ["name1", "name2"]}}

If no items match, respond with:
{{"items": []}}

INSTALLED SOFTWARE:
{candidates}"""


def detect_provider() -> tuple[str | None, str | None]:
    """Auto-detect which LLM provider is configured.

    Returns (provider_name, api_key) or (None, None).
    """
    cfg = load_config()

    if cfg.anthropic_api_key:
        return "anthropic", cfg.anthropic_api_key

    if cfg.openai_api_key:
        return "openai", cfg.openai_api_key

    return None, None


def _build_candidates_text(candidates: list[CleanupCandidate]) -> str:
    """Format candidates list for the LLM prompt."""
    lines: list[str] = []
    for c in candidates:
        desc = f" -- {c.description}" if c.description else ""
        lines.append(
            f"- {c.name} [{c.category}] "
            f"(Status: {c.status}){desc}"
        )
    return "\n".join(lines)


def _call_anthropic(
    prompt: str,
    candidates: list[CleanupCandidate],
    api_key: str,
) -> list[str] | None:
    """Call Claude API and return list of selected item names."""
    candidates_text = _build_candidates_text(candidates)
    system = SYSTEM_PROMPT.format(candidates=candidates_text)

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=LLM_TIMEOUT)
        data = json.loads(resp.read())
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        return _parse_llm_response(text)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise LLMError(f"Anthropic API error ({e.code}): {error_body}")
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"Anthropic API error: {e}")


def _call_openai(
    prompt: str,
    candidates: list[CleanupCandidate],
    api_key: str,
) -> list[str] | None:
    """Call OpenAI API and return list of selected item names."""
    candidates_text = _build_candidates_text(candidates)
    system = SYSTEM_PROMPT.format(candidates=candidates_text)

    body = json.dumps({
        "model": "gpt-4o-mini",
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=LLM_TIMEOUT)
        data = json.loads(resp.read())
        text = data["choices"][0]["message"]["content"]
        return _parse_llm_response(text)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise LLMError(f"OpenAI API error ({e.code}): {error_body}")
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"OpenAI API error: {e}")


def _parse_llm_response(text: str) -> list[str] | None:
    """Parse LLM response text into a list of item names.

    Validates that the response is well-formed JSON with the expected
    schema: {"items": ["name1", "name2"]}
    """
    text = text.strip()

    # Try to extract JSON from markdown code blocks
    if "```" in text:
        match = re.search(
            r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL,
        )
        if match:
            text = match.group(1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                return None
        else:
            return None

    if not isinstance(data, dict) or "items" not in data:
        return None

    items = data["items"]
    if not isinstance(items, list):
        return None

    # Validate all items are strings
    return [str(item) for item in items if isinstance(item, str)]


def query_llm(
    prompt: str,
    candidates: list[CleanupCandidate],
) -> list[str] | None:
    """Query the auto-detected LLM provider.

    Args:
        prompt: Natural language request (EN or ES)
        candidates: List of CleanupCandidate objects

    Returns:
        List of item names selected by the LLM, or None if no
        provider is available.

    Raises:
        LLMError: On API errors.
    """
    provider, api_key = detect_provider()
    if not provider or not api_key:
        return None

    if provider == "anthropic":
        items = _call_anthropic(prompt, candidates, api_key)
    elif provider == "openai":
        items = _call_openai(prompt, candidates, api_key)
    else:
        return None

    if items is None:
        return None

    # Validate: only return items that exist in the candidate list
    valid_names = {c.name for c in candidates}
    validated = [item for item in items if item in valid_names]

    return validated
