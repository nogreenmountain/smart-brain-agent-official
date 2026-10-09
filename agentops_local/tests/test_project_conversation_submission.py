import uuid

import pytest

from agentops_local.project_memory.conversations import validate_submission


def submission(**changes):
    values = dict(submission_id=str(uuid.uuid4()), title='修复记录',
                  messages=[{'role': 'user', 'content': '请修复显示问题'},
                            {'role': 'assistant', 'content': '已修复并验证'}],
                  task_result='修改页面并通过测试', model='client-model')
    values.update(changes)
    return values


def test_submission_has_stable_content_hash_and_client_declared_model():
    values = submission()
    first = validate_submission(**values)
    assert first.content_sha256 == validate_submission(**values).content_sha256
    assert first.model_source == 'client_declared'
    assert len(first.content_sha256) == 64
    assert first.content_sha256 != validate_submission(**(values | {'task_result': '另一结果'})).content_sha256


@pytest.mark.parametrize('role', ['system', 'developer', 'tool', 'User'])
def test_only_explicit_user_and_assistant_messages_are_allowed(role):
    with pytest.raises(ValueError, match='role'):
        validate_submission(**submission(messages=[{'role': role, 'content': 'text'}]))


@pytest.mark.parametrize('changes', [
    {'submission_id': 'not-a-uuid'}, {'messages': []}, {'title': ''},
    {'messages': [{'role': 'user', 'content': '   '}]},
    {'messages': [{'role': 'user', 'content': 'text', 'uploaded_by': 'someone'}]},
    {'messages': [{'role': 'user', 'content': 'x' * 200_001}]},
    {'task_result': 'password=private-value'},
    {'messages': [{'role': 'assistant', 'content': 'sk-abcdefghijklmnop'}]},
    {'model': 'api_key=private-value'}, {'title': 'bad\x00title'},
])
def test_invalid_or_sensitive_submissions_are_rejected(changes):
    with pytest.raises(ValueError):
        validate_submission(**submission(**changes))


def test_missing_model_is_unknown_and_no_usage_is_accepted():
    value = validate_submission(**submission(model=None))
    assert value.model == 'unknown'
    assert value.model_source == 'unknown'
    with pytest.raises(TypeError):
        validate_submission(**submission(total_tokens=100))


@pytest.mark.parametrize('content', [
    '<think>private deliberation</think>Final answer',
    '<analysis>private deliberation</analysis>',
    '<reasoning>private reasoning</reasoning>',
    '### 思考过程\n先逐步分析内部方案',
    '### 工具输出\nstdout: internal output',
    'assistant channel=analysis\ninternal reasoning',
    '<tool_call>{"name":"exec"}</tool_call>',
    '```json\n{"tool_calls":[]}\n```',
    '<system>internal instructions</system>',
    '[analysis] internal steps',
    '[COMMENTARY] progress update',
    '【思考过程】先分析内部方案',
    '[tool_result] internal output',
])
def test_internal_reasoning_and_non_conversation_envelopes_are_rejected(content):
    with pytest.raises(ValueError, match='summary|internal'):
        validate_submission(**submission(messages=[{'role':'assistant','content':content}]))


@pytest.mark.parametrize('changes', [
    {'messages':[{'role':'user','content':'问' * 301}]},
    {'messages':[{'role':'assistant','content':'答' * 601}]},
    {'task_result':'结' * 301},
    {'messages':[{'role':'user','content':'a'}, {'role':'assistant','content':'b'}, {'role':'user','content':'c'}]},
    {'messages':[{'role':'assistant','content':'b'}, {'role':'user','content':'a'}]},
    {'messages':[{'role':'assistant','content':'a'}, {'role':'assistant','content':'b'}]},
])
def test_summary_limits_reject_instead_of_silently_truncating(changes):
    with pytest.raises(ValueError):
        validate_submission(**submission(**changes))


def test_visible_request_and_final_answer_boundary_is_preserved():
    values=submission(messages=[{'role':'user','content':'问' * 300}, {'role':'assistant','content':'答' * 600}], task_result='结' * 300)
    result=validate_submission(**values)
    assert result.messages==values['messages'] and result.task_result==values['task_result']
