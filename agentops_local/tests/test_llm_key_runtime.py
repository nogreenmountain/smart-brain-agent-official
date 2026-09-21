import importlib
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def runtime():
    return importlib.import_module('agentops_local.ai_usage.llm_key_runtime')


def test_runtime_builds_only_from_server_configuration_without_network(monkeypatch):
    m=runtime(); iid=str(uuid.uuid4())
    monkeypatch.setenv('SB_LLM_GATEWAY_INSTANCE_ID',iid)
    monkeypatch.setenv('SB_LLM_GATEWAY_MANAGEMENT_URL','http://127.0.0.1:4000')
    monkeypatch.setenv('SB_LLM_GATEWAY_MASTER_KEY','synthetic-master')
    with Session(create_engine('sqlite://')) as orm:
        service=m.build_service(orm)
        assert service.instance_id==iid
        assert service.gateway.models==['gpt-5.6-sol','gpt-5.6-terra','gpt-5.6-luna','gpt-6-astra']
        service.close()


@pytest.mark.parametrize('field,value', [('SB_LLM_GATEWAY_INSTANCE_ID','invalid'),('SB_LLM_GATEWAY_MANAGEMENT_URL','http://public.example'),('SB_LLM_GATEWAY_MASTER_KEY','')])
def test_runtime_invalid_config_is_sanitized_and_never_falls_back(monkeypatch,field,value):
    m=runtime()
    monkeypatch.setenv('SB_LLM_GATEWAY_INSTANCE_ID',str(uuid.uuid4()))
    monkeypatch.setenv('SB_LLM_GATEWAY_MANAGEMENT_URL','http://127.0.0.1:4000')
    monkeypatch.setenv('SB_LLM_GATEWAY_MASTER_KEY','synthetic-master')
    monkeypatch.setenv(field,value)
    with Session(create_engine('sqlite://')) as orm:
        with pytest.raises(Exception,match='gateway_configuration_unavailable') as error:
            m.build_service(orm)
    assert 'synthetic-master' not in str(error.value)
