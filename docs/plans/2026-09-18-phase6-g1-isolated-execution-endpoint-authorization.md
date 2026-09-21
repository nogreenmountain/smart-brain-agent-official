# Phase 6 G1 — isolated execution endpoint authorization request

## Current state

The repair candidate is locally verified, but Claude Code correctly stopped before any remote action because no current, approved isolated execution endpoint or runner was available.

Current status:

```text
Phase 6 G1 P0 identity qualification: blocked / not qualified
G1-P1: not allowed
Mock gate: not started
Provider/model validation: not started
G2: not allowed
Gray rollout: not allowed
Production release: not allowed
```

This request is for the missing execution identity only. It is not permission to run the G1 PG gate, mock gate, provider calls, or model calls.

## What must be supplied by the environment owner

The environment owner must provide a current, non-production execution context with all of the following fields. Do not infer any field from historical artifacts.

```yaml
authorization:
  approved: false
  approver_name: ""
  approver_role: ""
  ticket_or_change_id: ""
  approved_at: ""
  expires_at: ""

execution_endpoint:
  environment: "isolated-non-production"
  host_or_context_id: ""
  transport: ""
  runner_path: ""
  runner_sha256_or_manifest: ""
  command_allowlist_reference: ""
  current_working_directory: ""

isolated_target:
  compose_project: "smartbrain-llm-pilot"
  compose_project_root: "/srv/smartbrain-llm-pilot"
  gateway_selector: "smartbrain.scope=isolated-pilot AND com.docker.compose.project=smartbrain-llm-pilot AND com.docker.compose.service=gateway"
  postgres_selector: "smartbrain.scope=isolated-pilot AND com.docker.compose.project=smartbrain-llm-pilot AND com.docker.compose.service=gateway-db"
  mock_selector: "smartbrain.scope=isolated-pilot AND com.docker.compose.project=smartbrain-llm-pilot AND com.docker.compose.service=mock-upstream"

scope:
  target_resolution_readonly: true
  file_repair_only_under_compose_project_root: false
  service_start_stop_restart: false
  postgres_readonly_preflight: false
  postgres_gate: false
  mock_requests: false
  gateway_requests: false
  provider_requests: false
  real_model_requests: false
  production_access: false
  secret_output: false
```

`approved` must remain `false` until the endpoint, runner, target selectors, approver, ticket, and expiry are filled by the environment owner.

## Endpoint acceptance criteria

The endpoint is acceptable only if all conditions below are true:

1. It is demonstrably non-production and cannot resolve to `smartbrain-prod`.
2. It can resolve the current Compose project and `smartbrain.scope=isolated-pilot` objects without accepting arbitrary user-supplied container IDs.
3. Its runner path and SHA/manifest are recorded before execution.
4. The initial command allowlist permits only sanitized read-only identity discovery.
5. It does not require reading or printing `.env`, API keys, tokens, cookies, authorization headers, database passwords, or raw prompt/response content.
6. It records every command, exit code, target selector, and timestamp.
7. It cannot target production Docker, production PostgreSQL, production systemd, production nginx, or production tunnels.
8. It has a separate, explicit approval before any file repair or service lifecycle operation.

## First allowed operation after approval

The first operation is a fresh P0 identity snapshot only. It must resolve and record:

- current gateway container, image, immutable digest, state, labels, network, and mounts;
- current PostgreSQL container, database, `current_user`, server version, and non-sensitive registration identity;
- current mock container and network membership;
- current runner identity and source/config/policy manifest status;
- whether the three repair target files exist and their SHA-256 values.

No file write, start, stop, restart, recreate, Docker exec, PostgreSQL write, gateway request, mock request, provider request, or model request is allowed in this first operation.

The output must be saved as a new local artifact, for example:

```text
E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-execution-preflight-r1.json
E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-execution-preflight-r1.log
```

## Second approval required for repair

Even if the first preflight succeeds, Claude Code must stop and wait for a second explicit approval before restoring files or starting the isolated Gateway. That second approval must name:

- the exact isolated host/context;
- the exact Compose project root;
- the exact three allowed file paths;
- the authoritative source manifest and SHA-256 values;
- whether service start/recreate is allowed;
- the rollback/stop condition;
- the expiry time.

No historical trusted-r1 policy, runner, container, or SHA may be used to fill a missing current identity. If the current G1 policy requirement cannot be satisfied from a unique current source manifest, the result remains blocked.

## Explicit exclusions

The following are not acceptable substitutes for an isolated execution endpoint:

- SSH alias `smartbrain-prod`;
- any production host or production Docker socket;
- any historical trusted-r1 container;
- any historical runner or tunnel;
- a manually supplied container ID without current selector verification;
- a database URL supplied in chat or an unverified environment variable;
- a local artifact path presented as proof of a remote runtime identity.

## Fixed GPT-6 policy

The endpoint request does not change model policy. GPT-6 must remain:

```text
status=disabled_by_operator
executed=false
request_count=0
fallback_used=false
```

No model request is part of this endpoint authorization.

## Required response from the environment owner

Return exactly:

```text
authorization.approved = true/false
approver = <name and role>
ticket_or_change_id = <id>
expires_at = <ISO-8601>
execution_endpoint = <non-production host/context identity>
transport = <approved runner transport>
approved_runner = <path and SHA/manifest>
gateway_selector = <selector>
postgres_selector = <selector>
mock_selector = <selector>
production_target_excluded = true/false
first_scope = readonly_identity_preflight_only
second_repair_approval_required = true
```

Until this response is complete and independently verified, the task remains blocked and no remote action is authorized.