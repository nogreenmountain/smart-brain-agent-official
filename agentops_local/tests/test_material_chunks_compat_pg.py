"""Real SQL compatibility checks against a named isolated synthetic database."""
import ast
import os
from pathlib import Path
import uuid

import pytest
from sqlalchemy import create_engine, text


def query_builder():
    source = ast.parse((Path(__file__).parents[1] / 'wiki_mcp/operations.py').read_text(encoding='utf-8'))
    selected = [n for n in source.body if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MATERIAL_CHUNKS_SQL' for t in n.targets)) or (isinstance(n, ast.FunctionDef) and n.name == '_material_chunk_sql')]
    assert len(selected) == 2, 'material reader compatibility query required'
    scope = {'text': text}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<material-reader>', 'exec'), scope)
    return scope['_material_chunk_sql']


@pytest.fixture(scope='module')
def engine():
    dsn = os.environ.get('SB_MATERIAL_READER_TEST_DSN')
    if not dsn:
        pytest.skip('named isolated material reader PostgreSQL required')
    db = create_engine(dsn)
    assert db.url.host == '127.0.0.1' and db.url.database == 'sb_material_reader_test_r1'
    with db.begin() as c:
        c.exec_driver_sql('''CREATE TABLE IF NOT EXISTS public.document_chunks (
          id uuid PRIMARY KEY,document_id uuid,project_id uuid,chunk_index integer,
          content text,source_page integer,source_line integer,created_at timestamptz DEFAULT now());
          CREATE TABLE IF NOT EXISTS public.document_chunks_v2 (
          id uuid PRIMARY KEY,document_id uuid,project_id uuid,chunk_index integer,
          content text,source_page integer,source_line integer,heading_path text,
          content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple',content)) STORED,
          created_at timestamptz DEFAULT now());''')
    yield db
    db.dispose()


@pytest.mark.parametrize('mode', ['legacy', 'v2', 'both'])
def test_document_and_lexical_search_read_one_preferred_generation(engine, mode):
    build = query_builder()
    pid, did = uuid.uuid4(), uuid.uuid4()
    with engine.begin() as c:
        for table in (['document_chunks'] if mode == 'legacy' else ['document_chunks_v2'] if mode == 'v2' else ['document_chunks', 'document_chunks_v2']):
            c.execute(text('INSERT INTO public.' + table + '(id,document_id,project_id,chunk_index,content,source_page,source_line) VALUES (:id,:d,:p,0,:content,1,2)'), {'id': uuid.uuid4(), 'd': did, 'p': pid, 'content': 'syntheticneedle ' + table})
        rows = c.execute(build('SELECT c.content,c.source_page,c.source_line FROM public.document_chunks_v2 c WHERE c.project_id=:p AND c.document_id=:d'), {'p': pid, 'd': did}).all()
        assert len(rows) == 1
        assert rows[0].content == 'syntheticneedle ' + ('document_chunks' if mode == 'legacy' else 'document_chunks_v2')
        assert rows[0].source_page == 1 and rows[0].source_line == 2
        hits = c.execute(build("SELECT c.id FROM public.document_chunks_v2 c WHERE c.project_id=:p AND c.document_id=:d AND c.content_tsv @@ plainto_tsquery('simple', 'syntheticneedle')"), {'p': pid, 'd': did}).all()
        assert len(hits) == 1


def test_other_project_v2_never_suppresses_or_leaks_legacy_rows(engine):
    build = query_builder()
    pid, other, did = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with engine.begin() as c:
        for table, project, content in [('document_chunks', pid, 'authorized synthetic'), ('document_chunks_v2', other, 'other project synthetic')]:
            c.execute(text('INSERT INTO public.' + table + '(id,document_id,project_id,chunk_index,content) VALUES (:id,:d,:p,0,:c)'), {'id': uuid.uuid4(), 'd': did, 'p': project, 'c': content})
        rows = c.execute(build('SELECT c.content FROM public.document_chunks_v2 c WHERE c.project_id=:p AND c.document_id=:d'), {'p': pid, 'd': did}).all()
        assert [r.content for r in rows] == ['authorized synthetic']


def test_unrelated_material_queries_are_unchanged():
    build = query_builder()
    sql = 'SELECT id FROM public.projects WHERE id=:p'
    assert str(build(sql)) == sql


def test_actual_version_diff_sql_reads_legacy_and_v2(engine):
    build = query_builder()
    tree = ast.parse((Path(__file__).parents[1] / 'wiki_mcp/operations.py').read_text(encoding='utf-8'))
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'compare_document_versions')
    sql = next(n.value for n in ast.walk(method) if isinstance(n, ast.Constant) and isinstance(n.value, str) and 'WITH old_chunks AS' in n.value)
    pid, old, new = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with engine.begin() as c:
        for table, did, index, content in [('document_chunks', old, 0, 'before'), ('document_chunks', old, 1, 'removed'), ('document_chunks_v2', new, 0, 'after'), ('document_chunks_v2', new, 2, 'added')]:
            c.execute(text('INSERT INTO public.' + table + '(id,document_id,project_id,chunk_index,content) VALUES (:id,:d,:p,:i,:c)'), {'id': uuid.uuid4(), 'd': did, 'p': pid, 'i': index, 'c': content})
        rows = c.execute(build(sql), {'project_id': pid, 'from_document_id': old, 'to_document_id': new}).all()
        assert [(r.chunk_index, r.change_type) for r in rows] == [(0, 'changed'), (1, 'removed'), (2, 'added')]
