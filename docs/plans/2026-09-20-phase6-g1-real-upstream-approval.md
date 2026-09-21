# Phase 6 / G1 — current isolated real-upstream approval package

## Current evidence

- Current Gateway: `smartbrain-llm-pilot-gateway-1`, container `cdc3c4fc476bf15a39cb5fab450c93095e72c68610e6645976ceb96e9c397e90`.
- Current image: `ghcr.io/berriai/litellm:v1.100.1@sha256:a3715fa7ad8387941ab697259bd2881d68931657247a41984f90fae6d11c62bf`.
- Current config is synthetic-only: `pilot-mock` → `http://mock-upstream:8080/v1`.
- Read-only catalog probe on September 20, 2026 returned HTTP 200 from `http://192.168.10.146:9000/v1/models`; Sol/Terra/Luna were present and GPT-6 was absent.
- No provider/model request has been sent.
- Existing `smartbrain-llm-egress-20260915-r1` contains historical container `d0d873…`; it is not reused.

## Required second approval

The operator must approve all of the following as one isolated-only change:

1. Create an empty bridge network named `smartbrain-llm-egress-g1-r2` with label `smartbrain.scope=isolated-model-pilot` and ICC disabled.
2. Connect only the current Gateway container `cdc3c4fc…` to that network.
3. Install a candidate LiteLLM config under the current isolated Compose project, using `PILOT_UPSTREAM_KEY` from a protected environment source. Do not print or copy the key into evidence.
4. Recreate/restart only the current isolated Gateway, after recording a rollback copy and SHA-256 of the current config.
5. Send at most one minimum request to each of `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna`; retries and fallback must remain disabled.
6. Do not send any request to `gpt-6-astra`; keep it disabled by operator.

The approval must identify the approver, ticket/change ID, expiry, exact host, exact Compose project, and the protected upstream credential source. A relay catalog response alone is not approval to mutate the Gateway or send model requests.

## Prompt for the isolated execution engineer

```text
You are executing Phase 6 / G1 real-upstream validation for the current isolated Gateway only.

Authoritative source:
D:\\AgentOpsServer\\AgentOps\\app

Current isolated selector:
smartbrain.scope=isolated-pilot AND com.docker.compose.project=smartbrain-llm-pilot AND com.docker.compose.service=gateway

Current Gateway container:
cdc3c4fc476bf15a39cb5fab450c93095e72c68610e6645976ceb96e9c397e90

Approved upstream catalog evidence (read-only, September 20, 2026):
http://192.168.10.146:9000/v1/models returned HTTP 200; gpt-5.6-sol, gpt-5.6-terra, and gpt-5.6-luna were present; gpt-6-astra was absent.

Before any mutation:
1. Re-resolve the current Gateway by the exact selector. Stop if zero, multiple, non-isolated, or historical objects match.
2. Record current container ID, image digest, source/config/policy hashes, network membership, and rollback copy.
3. Confirm the new egress network smartbrain-llm-egress-g1-r2 does not exist or is empty. Do not use smartbrain-llm-egress-20260915-r1 and do not connect historical container d0d873d3… .
4. Confirm the protected upstream key source exists without printing its value. Never read or emit the key, Authorization, cookies, prompts, or raw responses.

Candidate config rules:
- Configure only gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna.
- Use api_base http://192.168.10.146:9000/v1.
- Use api_key os.environ/PILOT_UPSTREAM_KEY.
- Keep num_retries=0, router retries=0, and no fallback.
- Do not add gpt-6-astra. Preserve status=disabled_by_operator, executed=false, request_count=0, fallback_used=false.
- Keep trusted_identity.gateway_guard and the current instance/source/endpoint identity unchanged.

Allowed lifecycle scope:
- only the current isolated Gateway container;
- no production containers, database, systemd, timer, nginx, route, Key, or employee traffic;
- no historical Gateway, runner, tunnel, or network.

Validation order after the second approval:
1. Create the new isolated egress network and connect only the current Gateway.
2. Install the candidate config with a reversible backup and verify SHA-256.
3. Restart/recreate only the current Gateway and wait for health.
4. Perform exactly one minimum request for Sol, Terra, and Luna. Use no retries and no fallback.
5. Record HTTP status, provider/model identity, request count, failure reason, and usage provenance without storing secrets or raw content.
6. If any model fails, record the failure and stop; do not substitute another model and do not continue to G2.
7. Revoke any temporary test credential in a finally path and prove no active test credential remains.
8. Restore the synthetic-only config and disconnect/remove the new egress network unless a separate retention approval says otherwise.

Do not claim G1 complete, gray rollout, or production readiness unless all three real-model requests pass and the final state is independently verified.
```

## Current gate

Until the second approval is recorded, the correct state is:

```text
P0 qualified: yes
P1 isolated PostgreSQL: passed
Mock gate: passed
Real Sol/Terra/Luna: blocked pending isolated repair approval
GPT-6: disabled_by_operator, zero requests, no fallback
G1 complete: no
G2 / gray / production: not allowed
```
