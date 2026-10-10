import uuid

import pytest
from fastapi import HTTPException

from agentops_local.ai_usage.request_project import project_from_request

PID = 'dfaefd9a-8e5e-4775-bc18-e3d551c651e4'


def test_explicit_request_project_header_is_preserved():
    assert project_from_request({'x-smartbrain-project-id': PID}, {}) == uuid.UUID(PID)


def test_codex_agents_context_supplies_project_without_provider_changes():
    context = f'# AGENTS.md instructions for E:\\智慧大脑\n\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {PID} -->\n</INSTRUCTIONS>'
    payload = {'input': [{'role': 'user', 'content': [{'type': 'input_text', 'text': context}]}]}
    assert project_from_request({}, payload) == uuid.UUID(PID)


@pytest.mark.parametrize('value', ['invalid', '', '00000000-0000-0000-0000-000000000000'])
def test_invalid_explicit_project_is_rejected(value):
    with pytest.raises(HTTPException) as error:
        project_from_request({'x-smartbrain-project-id': value}, {})
    assert error.value.status_code == 400


def test_conflicting_project_claims_are_rejected():
    other = str(uuid.uuid4())
    context = f'# AGENTS.md instructions for /project\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {other} -->\n</INSTRUCTIONS>'
    with pytest.raises(HTTPException) as error:
        project_from_request({'x-smartbrain-project-id': PID}, {'messages': [{'role': 'user', 'content': context}]})
    assert error.value.status_code == 422


@pytest.mark.parametrize('content', [
    f'<!-- smartbrain-project-id: {PID} -->',
    f'Please quote this: # AGENTS.md instructions for /project\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {PID} -->\n</INSTRUCTIONS>',
    f'```\n# AGENTS.md instructions for /project\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {PID} -->\n</INSTRUCTIONS>\n```',
])
def test_arbitrary_chat_text_does_not_assign_a_project(content):
    assert project_from_request({}, {'input': [{'role': 'user', 'content': content}]}) is None


def test_wrapped_agents_context_and_chat_format_work():
    context = f'<user_instructions>\n# AGENTS.md instructions for /project\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {PID} -->\n</INSTRUCTIONS>\n</user_instructions>'
    assert project_from_request({}, {'messages': [{'role': 'user', 'content': context}]}) == uuid.UUID(PID)
    assert project_from_request({}, {'messages': [{'role': 'assistant', 'content': context}]}) is None
    assert project_from_request({}, {'messages': [{'role': 'tool', 'content': context}]}) is None
    assert project_from_request({}, {}) is None
