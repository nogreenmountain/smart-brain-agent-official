import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('render_sql', ROOT / 'deploy/current/render_sql.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_clickhouse_private_password_escaped_for_sql_not_shell():
    assert m.render("PASSWORD '__SET_CLICKHOUSE_PASSWORD__'", {'CLICKHOUSE_PASSWORD': "a'b\\c$HOME"}) == "PASSWORD 'a\\'b\\\\c$HOME'"


def test_no_missing_secret_fallback():
    import pytest
    with pytest.raises(ValueError):
        m.render("PASSWORD '__SET_CLICKHOUSE_PASSWORD__'", {})
