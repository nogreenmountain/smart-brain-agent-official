"""Dedicated registered-member personal gateway entry; no business worker startup."""
from agentops.api.routes.v4 import ai_gateway
from agentops.api.personal_gateway_scope import build_app

app = build_app(ai_gateway)
