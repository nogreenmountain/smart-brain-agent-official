"""Read an explicit per-request project claim; authorization is separate."""
from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException


def agents_instructions(value: str) -> str | None:
    """Recognize a standalone Codex rules message, never arbitrary chat text."""
    value = value.strip()
    if value.startswith('<user_instructions>'):
        if not value.endswith('</user_instructions>'):
            return None
        value = value[len('<user_instructions>'):-len('</user_instructions>')].strip()
    match = re.fullmatch(r'# AGENTS\.md instructions for [^\r\n]+\r?\n\s*<INSTRUCTIONS>\s*(.*?)\s*</INSTRUCTIONS>', value, re.DOTALL)
    return match.group(1) if match else None


def _user_text(payload: dict[str, Any]):
    messages = payload.get('messages', payload.get('input', []))
    if not isinstance(messages, list):
        return
    for item in messages:
        if not isinstance(item, dict) or item.get('role') != 'user':
            continue
        content = item.get('content')
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get('type') in {'input_text', 'text'} and isinstance(part.get('text'), str):
                    yield part['text']


def project_from_request(headers: Mapping[str, str], payload: dict[str, Any]) -> uuid.UUID | None:
    values = [v for k, v in headers.items() if k.lower() == 'x-smartbrain-project-id']
    for text in _user_text(payload):
        rules = agents_instructions(text)
        if rules is not None:
            values.extend(re.findall(r'^\s*<!--\s*smartbrain-project-id:\s*([^\r\n]*?)\s*-->\s*$', rules, re.MULTILINE))
    projects = set()
    for value in values:
        try:
            parsed = uuid.UUID(value.strip())
            if not parsed.int or str(parsed) != value.strip().lower():
                raise ValueError('canonical project UUID required')
        except (ValueError, AttributeError, TypeError) as error:
            raise HTTPException(400, 'invalid_project_id') from error
        projects.add(parsed)
    if len(projects) > 1:
        raise HTTPException(422, 'conflicting_project_ids')
    return next(iter(projects), None)
