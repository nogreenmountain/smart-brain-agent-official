import importlib.util
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

import agentops_local
import pytest
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture(scope='module')
def operations():
    with patch.dict(sys.modules, {'agentops': agentops_local}):
        spec = importlib.util.spec_from_file_location('conversation_ops_test', Path(__file__).parents[1]/'wiki_mcp/operations.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def test_record_requires_write_scope_before_opening_session(operations):
    factory = Mock()
    with pytest.raises(PermissionError, match='wiki:propose'):
        operations.WikiOperations(session_factory=factory).record_conversation(
            user_id=uuid.uuid4(), scopes=['wiki:read'], project_id=str(uuid.uuid4()),
            submission_id=str(uuid.uuid4()), title='合成', messages=[{'role':'user','content':'合成'}])
    factory.assert_not_called()


@pytest.mark.parametrize('project', ['', None, 'name', 'invalid'])
def test_record_never_falls_back_to_default_project(operations, monkeypatch, project):
    monkeypatch.setenv('WIKI_MCP_DEFAULT_PROJECT_ID', str(uuid.uuid4()))
    factory = Mock()
    with pytest.raises(ValueError, match='project_id'):
        operations.WikiOperations(session_factory=factory).record_conversation(
            user_id=uuid.uuid4(), scopes=['wiki:propose'], project_id=project,
            submission_id=str(uuid.uuid4()), title='合成', messages=[{'role':'user','content':'合成'}])
    factory.assert_not_called()


def test_record_passes_authenticated_identity_and_committed_receipt(operations):
    orm, user, project = object(), uuid.uuid4(), uuid.uuid4()
    @contextmanager
    def factory():
        yield orm
    receipt = {'record_id':str(uuid.uuid4()), 'wiki_status':'published'}
    with patch.object(operations, 'save_project_conversation', return_value=receipt) as save:
        result = operations.WikiOperations(session_factory=factory).record_conversation(
            user_id=user, scopes=['wiki:read','wiki:propose'], project_id=str(project),
            submission_id=str(uuid.uuid4()), title='合成', messages=[{'role':'user','content':'合成'}])
    assert result == receipt
    assert save.call_args.kwargs['user_id'] == user
    assert save.call_args.kwargs['project_id'] == project
    assert save.call_args.args[0] is orm


def test_commit_failure_does_not_acknowledge_save_or_expose_database_details(operations):
    @contextmanager
    def factory():
        yield object()
        raise SQLAlchemyError('private database connection details')
    with patch.object(operations, 'save_project_conversation', return_value={'status':'saved'}):
        with pytest.raises(RuntimeError, match='record_save_failed') as error:
            operations.WikiOperations(session_factory=factory).record_conversation(
                user_id=uuid.uuid4(),scopes=['wiki:propose'],project_id=str(uuid.uuid4()),
                submission_id=str(uuid.uuid4()),title='合成',messages=[{'role':'user','content':'合成'}])
    assert 'private' not in str(error.value)
