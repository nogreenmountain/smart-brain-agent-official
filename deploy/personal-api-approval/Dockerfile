ARG BASE_IMAGE
FROM ${BASE_IMAGE}
USER 0
COPY --chown=10001:10001 --chmod=0644 ai_gateway.py /app/agentops/api/routes/v4/ai_gateway.py
RUN /app/.venv/bin/python -m py_compile /app/agentops/api/routes/v4/ai_gateway.py
USER 10001:10001
