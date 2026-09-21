"""Server-owned gateway configuration. The route feature flag defaults off."""
import os
import uuid

from sqlalchemy.orm import sessionmaker

from .litellm_management import LiteLLMManagement
from .llm_key_operations import KeyOperationError, KeyOperations


MODELS = ('gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna', 'gpt-6-astra')


def build_service(orm):
    try:
        instance_id = str(uuid.UUID(os.environ['SB_LLM_GATEWAY_INSTANCE_ID']))
        gateway = LiteLLMManagement(os.environ['SB_LLM_GATEWAY_MANAGEMENT_URL'],
                                   os.environ['SB_LLM_GATEWAY_MASTER_KEY'], models=MODELS)
    except (KeyError, ValueError, TypeError):
        raise KeyOperationError('gateway_configuration_unavailable', 503) from None
    return KeyOperations(sessionmaker(bind=orm.get_bind()), gateway, instance_id=instance_id)
