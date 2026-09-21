# Phase 6 / G1-R3 — identity repair and isolated real-upstream approval

## Current verified state

- The previous G1-R2 real-upstream attempt consumed the approved Sol allowance and returned HTTP 400. Terra and Luna were not sent. GPT-6 remained disabled and unused.
- The isolated Gateway is back in synthetic-only mode. The temporary egress network was removed, the Gateway is healthy, and no provider request is pending.
- Current synthetic-only rollback hashes:
  - `litellm.pilot.yaml`: `e951f2b775df25b97fbfa5b9f577376978a591838d531ebb0916ce6792ab41ae`
  - `compose.pilot.yaml`: `01a24c291295690b3a8f853abde0454f09e4cb07829016d49f293c7fb9672431`
- The failed real-upstream copies remain on the server and must not be deleted:
  - `.g1-r2-failed-real.litellm.yaml`
  - `.g1-r2-failed-real.compose.yaml`

## Local repair completed

Root: `D:\AgentOpsServer\AgentOps\app\deploy\llm-gateway`

The policy now:

1. Stores authenticated identity in `litellm_metadata` for every call type.
2. Removes client/provider-facing `metadata` before returning the payload.
3. Keeps the server-authenticated `user` only for non-Responses calls.
4. Removes `metadata` from `proxy_server_request.body` and mirrors trusted identity in `litellm_metadata`.
5. Preserves Responses behavior, input immutability, and propagation-header filtering.

Local evidence:

- New Red test: `test_chat_identity_stays_in_internal_metadata_without_provider_metadata`.
- Identity-policy tests: `7 passed`.
- Full authoritative gateway test directory: `38 passed` with `PYTHONPATH` set to the authoritative gateway root.
- `py_compile`: passed for `identity_policy.py` and `trusted_identity.py`.
- New source hash for `identity_policy.py`: `435b389d246afa00f027ef71f654e8b6a0eb822481cfc91995f0ba898d333b17`.
- `trusted_identity.py` unchanged: `adc8632f70b3da7e7fad71ddcbea2e3d1fed70ba4a5b36c3fac88f7695d8825`.

These are local candidate results only. They do not qualify G1 and do not authorize a server restart or provider request.

## Required new approval

Create a new approval/change record because R2 consumed the Sol allowance. The approval must explicitly identify the operator, ticket/change ID, expiry, exact host, exact Compose project, and protected upstream credential source.

Approval scope:

1. Re-resolve the current Gateway using the exact isolated selector:
   `smartbrain.scope=isolated-pilot`,
   `com.docker.compose.project=smartbrain-llm-pilot`,
   `com.docker.compose.service=gateway`.
   Stop on zero, multiple, historical, or non-isolated matches.
2. Only the newly repaired candidate source/config may be used. Do not copy any historical `trusted-r1` files or reuse the old egress network/container.
3. Create `smartbrain-llm-egress-g1-r3` as an isolated bridge with the approved ICC policy and connect only the current Gateway.
4. Install a candidate configuration that contains only:
   `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna`.
   Use the protected `PILOT_UPSTREAM_KEY` source without printing or persisting its value in evidence.
5. Keep `num_retries=0`, router retries at zero, and fallback disabled.
6. Permit at most one minimum request per model, in this order: Sol, Terra, Luna. If any request fails, record the sanitized failure and stop; do not continue to the next model.
7. Do not request `gpt-6-astra`. Preserve:
   `status=disabled_by_operator`, `executed=false`, `request_count=0`, `fallback_used=false`.
8. Do not touch production containers, databases, systemd/timer, nginx, routes, employee Keys, or employee traffic.
9. In a finally path, revoke any temporary test credential, restore the synthetic-only config, verify health, disconnect/remove the new egress network, and delete only temporary merged-env material. Preserve the failed-real evidence copies.

## Mandatory evidence

Record only sanitized facts:

- resolved current container ID, immutable image digest, network membership, source/config/policy hashes, and runner identity;
- per-model HTTP status, provider/model identity, request count, retry count, fallback flag, and usage provenance;
- no secrets, Authorization headers, cookies, prompts, raw provider responses, or full environment variables;
- final synthetic-only hashes, healthy state, no egress membership, and no active temporary credential.

## Gate decision

Until all three newly authorized requests succeed and the final state is independently verified:

```text
G1: incomplete
G2: not allowed
gray rollout: not allowed
production release: not allowed
```

If any model fails, retain the failure evidence, restore synthetic-only state, and stop. Do not claim partial real-model qualification as G1 completion.
