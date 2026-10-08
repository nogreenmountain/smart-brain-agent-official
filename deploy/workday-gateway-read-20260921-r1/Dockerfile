FROM smartbrain/api:workday-gateway-body-20260910-r2

USER 0
COPY ai_usage.py /app/agentops/api/routes/v4/ai_usage.py
COPY ai_gateway.py /app/agentops/api/routes/v4/ai_gateway.py
COPY ai_chat.py /app/agentops/api/routes/v4/ai_chat.py
COPY personal_gateway_scope.py /app/agentops/api/personal_gateway_scope.py
RUN /app/.venv/bin/python -m py_compile \
    /app/agentops/api/routes/v4/ai_usage.py \
    /app/agentops/api/routes/v4/ai_gateway.py \
    /app/agentops/api/routes/v4/ai_chat.py \
    /app/agentops/api/personal_gateway_scope.py
USER 10001:10001
