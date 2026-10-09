"""Render private ClickHouse DDL to a protected file outside checkout."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify


def render(text, values):
    value = values.get('CLICKHOUSE_PASSWORD')
    if not value or '__SET_' in value:
        raise ValueError('CLICKHOUSE_PASSWORD required')
    escaped = value.replace('\\', '\\\\').replace("'", "\\'")
    return text.replace('__SET_CLICKHOUSE_PASSWORD__', escaped)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--env-file', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    try:
        dest = Path(a.output).resolve()
        if verify.check_private_root(verify.ROOT, dest.parent):
            raise ValueError('private output in checkout')
        values, errors = verify.read_env(a.env_file)
        if errors:
            raise ValueError('invalid private environment')
        rendered = render((verify.HERE / 'clickhouse/schema-current.sql').read_text(), values)
        with dest.open('x', encoding='utf-8') as f:
            f.write(rendered)
        dest.chmod(0o600)
        print('Private SQL file rendered; values withheld')
        return 0
    except (OSError, ValueError):
        print('SQL render refused: invalid prerequisites or output already exists')
        return 1


if __name__ == '__main__':
    sys.exit(main())
