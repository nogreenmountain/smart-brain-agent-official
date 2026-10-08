ARG BASE_IMAGE=smartbrain-personal-key-fix:20260915-r1
FROM ${BASE_IMAGE}

USER 0:0

# This image is an additive overlay on the currently running production API.
# It replaces only the personal gateway route and adds the durable operation
# state machine/reconciler modules. No credentials or rollout rows are baked
# into the image.
COPY agentops_local/api/routes/v4/ai_gateway.py /app/agentops/api/routes/v4/ai_gateway.py
COPY agentops_local/ai_usage/gateway.py /app/agentops/ai_usage/gateway.py
COPY agentops_local/ai_usage/gateway_content.py /app/agentops/ai_usage/gateway_content.py
COPY agentops_local/ai_usage/gateway_tokens.py /app/agentops/ai_usage/gateway_tokens.py
COPY agentops_local/ai_usage/litellm_management.py /app/agentops/ai_usage/litellm_management.py
COPY agentops_local/ai_usage/llm_key_operations.py /app/agentops/ai_usage/llm_key_operations.py
COPY agentops_local/ai_usage/llm_key_quota.py /app/agentops/ai_usage/llm_key_quota.py
COPY agentops_local/ai_usage/llm_key_runtime.py /app/agentops/ai_usage/llm_key_runtime.py
COPY agentops_local/ai_usage/llm_key_reconcile_worker.py /app/agentops/ai_usage/llm_key_reconcile_worker.py

RUN chown -R 10001:10001 /app/agentops/api/routes/v4 /app/agentops/ai_usage
USER 10001:10001
