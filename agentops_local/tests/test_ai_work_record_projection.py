from agentops_local.ai_usage.domain import UsageMessage
from agentops_local.ai_usage.work_record_projection import select_work_record_messages


def test_work_record_keeps_real_prompt_and_final_summary_only():
    messages = [
        UsageMessage(
            role="user",
            content=(
                "The following is the Codex agent history added since your last approval assessment. "
                "Continue the same review conversation.\n\n"
                ">>> TRANSCRIPT DELTA START\n"
                "[30] tool record_project_conversation result: saved\n"
                ">>> TRANSCRIPT DELTA END\n\n"
                ">>> APPROVAL REQUEST START\n{\"tool\": \"get_page\"}\n"
                ">>> APPROVAL REQUEST END"
            ),
        ),
        UsageMessage(role="assistant", content="正在读取项目状态并核对记录。"),
        UsageMessage(role="user", content="只抓取我的提示词和最终总结，完整对话仍存入知识库。"),
        UsageMessage(role="assistant", content="已完成筛选规则设计，并保留知识库中的完整对话记录。"),
    ]

    visible = select_work_record_messages(messages)

    assert [(message.role, message.content) for message in visible] == [
        ("user", "只抓取我的提示词和最终总结，完整对话仍存入知识库。"),
        ("assistant", "已完成筛选规则设计，并保留知识库中的完整对话记录。"),
    ]
    combined = " ".join(message.content for message in visible)
    assert "TRANSCRIPT DELTA" not in combined
    assert "APPROVAL REQUEST" not in combined
    assert "tool" not in combined.lower()


def test_work_record_keeps_multiple_user_prompts_but_only_last_assistant():
    messages = [
        UsageMessage(role="user", content="第一条用户提示"),
        UsageMessage(role="assistant", content="中间进度，不应展示"),
        UsageMessage(role="user", content="补充输入"),
        UsageMessage(role="assistant", content="最终总结"),
    ]

    visible = select_work_record_messages(messages)

    assert [(message.role, message.content) for message in visible] == [
        ("user", "第一条用户提示"),
        ("user", "补充输入"),
        ("assistant", "最终总结"),
    ]


def test_work_record_does_not_drop_a_normal_prompt_that_mentions_tool_call():
    visible = select_work_record_messages([
        UsageMessage(role="user", content="请解释 tool_call 的用途"),
        UsageMessage(role="assistant", content="tool_call 用于表达工具调用结构。"),
    ])

    assert [message.content for message in visible] == [
        "请解释 tool_call 的用途",
        "tool_call 用于表达工具调用结构。",
    ]


def test_work_record_ignores_structured_approval_reply_and_uses_last_summary():
    visible = select_work_record_messages([
        UsageMessage(role="user", content="请检查发布状态"),
        UsageMessage(role="assistant", content='{"outcome":"allow"}'),
        UsageMessage(role="assistant", content="已核对发布状态，当前无需变更。"),
    ])

    assert [(message.role, message.content) for message in visible] == [
        ("user", "请检查发布状态"),
        ("assistant", "已核对发布状态，当前无需变更。"),
    ]


def test_work_record_extracts_user_text_after_embedded_review_envelope():
    visible = select_work_record_messages([
        UsageMessage(
            role="user",
            content=(
                "The following is the Codex agent history added since your last approval assessment.\n"
                ">>> TRANSCRIPT DELTA START\n[30] tool record_project_conversation result: saved\n"
                ">>> TRANSCRIPT DELTA END\n"
                ">>> APPROVAL REQUEST START\n{\"tool\": \"get_page\"}\n"
                ">>> APPROVAL REQUEST END\n"
                "**AI**\n{\"outcome\":\"allow\"}\n"
                "我只需要抓取我的提示词和最终总结。"
            ),
        ),
        UsageMessage(role="assistant", content="已按要求调整工作记录投影。"),
    ])

    assert [(message.role, message.content) for message in visible] == [
        ("user", "我只需要抓取我的提示词和最终总结。"),
        ("assistant", "已按要求调整工作记录投影。"),
    ]


def test_work_record_keeps_normal_json_final_summary():
    visible = select_work_record_messages([
        UsageMessage(role="user", content="请输出机器可读结果"),
        UsageMessage(role="assistant", content='{"status":"completed","items":["项目A"]}'),
    ])

    assert [(message.role, message.content) for message in visible] == [
        ("user", "请输出机器可读结果"),
        ("assistant", '{"status":"completed","items":["项目A"]}'),
    ]


def test_work_record_keeps_normal_json_prompt():
    visible = select_work_record_messages([
        UsageMessage(role="user", content='{"tool":"解释这个字段","value":42}'),
        UsageMessage(role="assistant", content="字段含义如下。"),
    ])

    assert [(message.role, message.content) for message in visible] == [
        ("user", '{"tool":"解释这个字段","value":42}'),
        ("assistant", "字段含义如下。"),
    ]


def test_work_record_keeps_normal_lines_that_start_with_runtime_like_words():
    visible = select_work_record_messages([
        UsageMessage(role="user", content="tool 是这个字段的业务名称\nretry reason 是接口字段"),
        UsageMessage(role="assistant", content="planned action 是下一步计划字段。"),
    ])

    assert [(message.role, message.content) for message in visible] == [
        ("user", "tool 是这个字段的业务名称\nretry reason 是接口字段"),
        ("assistant", "planned action 是下一步计划字段。"),
    ]
