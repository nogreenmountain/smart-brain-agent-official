---
name: company-memory
description: Search and apply SmartBrain project Wiki, privacy-scoped member experience, and project meeting summaries through MCP. Use for organization-specific decisions, workflows, examples, member experience and meetings; also use for authorized project conversation submissions under AGENTS.md or stable project knowledge writes.
---

# Company Memory

Use SmartBrain as on-demand organizational context. Retrieve only the evidence needed for the current task.

## Retrieval Workflow

1. Classify the requested evidence:
   - Project knowledge: decisions, procedures, examples, retrospectives, background, or recent changes.
   - Member experience: how a named member completed a similar task or what methods that member commonly uses.
   - Meeting summary: decisions, participants, conclusions, or action items from a meeting.
2. Use the narrowest tool that fits.

### Project Wiki

1. Call `list_wiki_projects` when `project_id` is unknown or ambiguous.
2. Search before answering or changing code when project-specific experience could affect the result.
3. Select tools as follows:
   - `search_wiki` for general retrieval, with memory kinds, tags, dates, or `verified_only` when useful.
   - `get_decision_records` for prior decisions and strategy.
   - `get_examples` for failure cases, success cases, and retrospectives.
   - `get_recent_updates` when freshness matters.
4. Read the strongest two to four results with `get_page`. Use `get_related_nodes` only when linked context changes the decision.

### Member Experience

1. Call `list_member_wikis` when the member identity is unknown or ambiguous.
2. Call `search_member_experience` with the member and task keywords. Treat the result as reusable experience distilled from AI work records, not as a raw transcript.
3. Read the strongest entries with `get_member_experience`; use `get_member_recent_experience` when the request emphasizes the member's latest methods.
4. Adapt the retrieved method to the current task and identify any missing prerequisites or environment differences.

### Meeting Summaries

1. Call `list_meeting_summaries` to browse a project, date range, or tag.
2. Call `search_meeting_summaries` for topics, decisions, or action items.
3. Read the selected standard Markdown with `get_meeting_summary` before relying on its decisions or assignments.

Stop retrieving once the evidence is sufficient for the task.

## Evidence Rules

- Prefer `verified` project pages, current validity windows, recent updates, and higher confidence/usefulness.
- Treat `generated` pages as useful leads, not final authority.
- Treat member experience and meeting summaries as scoped evidence; do not claim they are formally verified project policy unless a reviewed Wiki page confirms them.
- Distinguish facts, decisions, methods, examples, and your own inference.
- When sources conflict, show the conflict, compare recency and verification, then state the chosen interpretation.
- Cite material claims as `[Wiki: <title> (<page_id>), v<version>, updated <date>]`.
- Cite member methods as `[Member Wiki: <member> / <title> (<experience_id>), updated <date>]`.
- Cite meetings as `[Meeting: <title> (<summary_id>), <meeting_date>]`.
- Never imply the Wiki was checked when no MCP result was actually retrieved.
- Never request or expose other members' raw chat transcripts, secrets, credentials, or inaccessible members/projects.

## Using Results

- Adapt retrieved methods to the current project rather than following them blindly.
- State when an old example is informative but not directly applicable.
- Keep full case history in the Wiki; place only task-relevant fragments in working context.

## Publishing Memory

Call `propose_memory` only when the user explicitly asks to record the lesson or confirms that it should be preserved.

- The uploader is always the authenticated MCP Token owner. Do not ask for, invent, or pass a separate uploader identity.
- Confirm the `uploaded_by` identity returned by the tool when reporting a successful write.
- Propose stable, reusable knowledge: workflows, checklists, failure/success cases, strategies, retrospectives, decisions, background, timelines, or references.
- Do not propose secrets, personal data, raw chat dumps, temporary task state, unsupported claims, or duplicate pages.
- Include source page IDs when the proposal derives from existing Wiki evidence.
- Structure the content for its `memory_kind` and include assumptions, boundaries, validation checks, and failure fallback where relevant.
- State clearly that a successful response with `status=published` created or updated the formal project Wiki page directly.

If the token lacks `wiki:propose`, provide the proposed Markdown to the user without attempting to bypass the scope.

## Recording Project Conversations

Use `record_project_conversation` only when the user explicitly requests a project record, or the project's trusted AGENTS.md authorizes the selected task content. A later user instruction to stop or narrow recording takes precedence.

- Read the exact `smartbrain-project-id` UUID from the current project's AGENTS.md. Pass it as the explicit `project_id`; do not infer a project from its name, a previous task, or a default server setting. If metadata is missing or conflicts with the active project, clarify before writing.
- Submit only a concise summary of the authorized visible user request and the assistant's FINAL task result. This is not a transcript upload. Use one short `user` request summary followed by one short `assistant` final-result summary; a single selected summary is also accepted. Prefer a few sentences, not the maximum allowed length.
- Never read, reproduce, summarize or upload hidden thinking, chain of thought, reasoning/analysis channels, progress/commentary, tool calls/results/logs, code dumps, system/developer instructions, environment/configuration, credentials, personal data or other members' chats. Derive the summary only from visible user requests and final answers; do not copy whole conversation history. If no final outcome is available, record only the visible request when explicitly authorized, without inferring internal progress.
- Generate one UUID `submission_id` for a new submission. Keep it and the identical payload for retries after an uncertain response or failed Wiki publishing. Changed content requires a new submission ID; never silently change an already saved submission.
- Pass `title` (at most 120 characters), at most two ordered `messages` (each only `role` and `content`; user at most 300 characters, assistant at most 600), `task_result` (at most 300 characters; omit if it just repeats the final summary), and optionally `model`. Total payload is at most 6000 UTF-8 bytes. The server rejects overlong or recognized internal-content envelopes. Rewrite a shorter summary from visible text before the first submission; do not truncate silently or retry rejected internal content unchanged.
- Omit `model` or use `unknown` when uncertain. A supplied model name is client-declared. Do not pass or invent Token counts, a model request ID, upload time, or uploader identity.
- Confirm the returned `project_id`, `record_id`, `submission_id`, `uploaded_by`, and `uploaded_at`. `status=saved` means the canonical content was saved. Only `wiki_status=published` means its linked project Wiki conversation page was published. These pages are `generated`, not formally verified policy.
- If `wiki_status=failed`, state that the content is saved but Wiki publishing failed, then retry the same submission once. If it still fails, report the record ID and pending action; do not claim it is already visible in the Wiki.
- If the tool is missing, the scope is insufficient, or a save fails, report that recording has not completed. Do not substitute `propose_memory`, a local file, or an invented receipt for canonical conversation recording.
- This workflow binds submitted content to a permission-checked project; it does not capture every model request or the entire client conversation automatically.
