"""User-facing projection for AI work records.

The source chat and project conversation knowledge records remain complete.
This module only selects the compact prompt/final-summary view returned by the
AI work log endpoint.
"""

from __future__ import annotations

import re
from dataclasses import replace

try:
    from agentops.ai_usage.domain import UsageMessage
except ModuleNotFoundError:  # source-tree tests
    from agentops_local.ai_usage.domain import UsageMessage

_INTERNAL_CONTEXT_BLOCK = re.compile(
    r"<environment_context\b[^>]*>.*?</environment_context\s*>|"
    r"<external_codex_apps_open_page\b[^>]*>.*?</external_codex_apps_open_page\s*>",
    re.IGNORECASE | re.DOTALL,
)
_CONVERSATION_SPEAKER = re.compile(r"(?:^|\n)\s*\*\*(用户|AI|assistant|user)\*\*\s*\n?", re.IGNORECASE)
_WORK_RECORD_TRANSCRIPT_BLOCK = re.compile(
    r"(?:The following is the Codex agent history.*?\n)?\s*"
    r"(?:>>>\s*)?TRANSCRIPT DELTA START.*?"
    r"(?:>>>\s*)?TRANSCRIPT DELTA END",
    re.IGNORECASE | re.DOTALL,
)
_WORK_RECORD_APPROVAL_BLOCK = re.compile(
    r"(?:>>>\s*)?APPROVAL REQUEST START.*?"
    r"(?:>>>\s*)?APPROVAL REQUEST END",
    re.IGNORECASE | re.DOTALL,
)
_WORK_RECORD_INTERNAL_LINES = re.compile(
    r"^\s*(?:\[\d+\]\s+)?(?:tool|retry reason|planned action)\b.*$|"
    r"^\s*Reviewed Codex session id:.*$",
    re.IGNORECASE | re.MULTILINE,
)
_WORK_RECORD_INTERNAL_ONLY = re.compile(
    r"^(?:\x60\x60\x60(?:json|text)?\s*)?<\/?(?:think|analysis|reasoning|tool_call|tool_result|system)>.*(?:\s*\x60\x60\x60)?$",
    re.IGNORECASE | re.DOTALL,
)
_EMBEDDED_RUNTIME_SPEAKER = re.compile(
    r"(?:^|\n)\s*\*\*(?:AI|assistant)\*\*\s*\n+(?:(?:\s*(?:\{[^\n]*\}|\[[^\n]*\])\s*\n)+)?",
    re.IGNORECASE,
)
_APPROVAL_REPLY_LINE = re.compile(
    r"^\s*\{\s*[\"\x27]outcome[\"\x27]\s*:\s*[\"\x27](?:allow|deny)[\"\x27](?:\s*,\s*[^}]*)?\}\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _clean_visible_message(role: str, content: str) -> str:
    """Keep the user-facing exchange and remove agent/runtime envelopes."""
    cleaned = _INTERNAL_CONTEXT_BLOCK.sub("", content).strip()
    matches = list(_CONVERSATION_SPEAKER.finditer(cleaned))
    if matches:
        wanted = "用户" if role == "user" else "ai"
        selected = None
        for index, match in enumerate(matches):
            label = match.group(1).lower()
            normalized = "用户" if label in {"用户", "user"} else "ai"
            if normalized != wanted:
                continue
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(cleaned)
            selected = cleaned[start:end].strip()
            break
        if selected is not None:
            cleaned = selected
    return cleaned


def _clean_work_record_message(role: str, content: str) -> str:
    """Remove Codex runtime envelopes from the work-record projection only."""
    had_runtime_envelope = bool(
        _WORK_RECORD_TRANSCRIPT_BLOCK.search(content)
        or _WORK_RECORD_APPROVAL_BLOCK.search(content)
        or "The following is the Codex agent history" in content
    )
    cleaned = _clean_visible_message(role, content)
    cleaned = _WORK_RECORD_TRANSCRIPT_BLOCK.sub("", cleaned)
    cleaned = _WORK_RECORD_APPROVAL_BLOCK.sub("", cleaned)
    if had_runtime_envelope:
        cleaned = _WORK_RECORD_INTERNAL_LINES.sub("", cleaned)
    if had_runtime_envelope:
        cleaned = _EMBEDDED_RUNTIME_SPEAKER.sub("\n", cleaned)
        cleaned = _APPROVAL_REPLY_LINE.sub("", cleaned)
    cleaned = re.sub(
        r"^\s*(?:The following is the Codex agent history.*)$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    cleaned = re.sub(
        r"^\s*\\?>>>\s*(?:TRANSCRIPT|APPROVAL|TOOL|RETRY|PLANNED ACTION).*?$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return cleaned.strip()


def _is_internal_work_record_message(role: str, content: str) -> bool:
    lowered = content.lower().strip()
    if "transcript delta start" in lowered or "approval request start" in lowered:
        return True
    if role == "assistant" and any(marker in lowered for marker in (
        "assistant channel=analysis", "[commentary]", "[analysis]", "<think>",
        "<tool_call>", "<tool_result>",
    )):
        return True
    if role == "assistant" and (_WORK_RECORD_INTERNAL_ONLY.fullmatch(content.strip())
                                or _APPROVAL_REPLY_LINE.fullmatch(content.strip())):
        return True
    return False


def select_work_record_messages(messages: list[UsageMessage] | tuple[UsageMessage, ...]) -> tuple[UsageMessage, ...]:
    """Project a completed work record to prompts plus the final assistant summary.

    The source chat remains untouched; this selector is only used by the AI work
    log response. Internal Codex transcript, approval, tool and retry envelopes
    are omitted, while the last visible assistant message is treated as the
    task summary.
    """
    visible: list[UsageMessage] = []
    for message in messages:
        role = str(message.role or "").lower()
        if role not in {"user", "assistant"}:
            continue
        content = _clean_work_record_message(role, str(message.content or ""))
        if not content or _is_internal_work_record_message(role, content):
            continue
        visible.append(replace(message, role=role, content=content))
    users = [message for message in visible if message.role == "user"]
    final_assistant = next(
        (message for message in reversed(visible) if message.role == "assistant"),
        None,
    )
    return tuple(users + ([final_assistant] if final_assistant else []))

