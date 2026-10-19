# Build only after the current production image and release gates are verified.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

USER 0
COPY personal_gateway_scope.py /app/agentops/api/personal_gateway_scope.py
COPY personal_gateway_app.py /app/agentops/api/personal_gateway_app.py
RUN /app/.venv/bin/python -m py_compile \
    /app/agentops/api/personal_gateway_scope.py \
    /app/agentops/api/personal_gateway_app.py
USER 10001:10001
