"""Existing workday Gateway content reads; no ingestion or worker entrypoints."""
import os
from agentops.api.routes.v4 import ai_gateway, ai_usage
from agentops.api.personal_gateway_scope import allowed_users, build_app

app = build_app(ai_gateway, allowed_users(os.environ['SB_GATEWAY_ALLOWED_USER_IDS']),
                usage_route=ai_usage)
