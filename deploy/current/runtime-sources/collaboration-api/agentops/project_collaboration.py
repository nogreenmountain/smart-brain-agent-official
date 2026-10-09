"""Project instructions and reporting boundaries shared by the collaboration API."""
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import re

MAX_AGENTS_BYTES = 65536
SHANGHAI = timezone(timedelta(hours=8))

def render_agents(name: str, project_id: str) -> str:
    template = Path(__file__).with_name('project_agents_template.md').read_text(encoding='utf-8')
    values = {'PROJECT_NAME': name, 'PROJECT_ID': str(project_id)}
    return re.sub(r'\{\{(PROJECT_NAME|PROJECT_ID)\}\}', lambda match: values[match[1]], template)

def validate_agents(filename: str, payload: bytes) -> str:
    if filename != 'AGENTS.md':
        raise ValueError('文件名必须严格为 AGENTS.md（区分大小写）')
    if len(payload) > MAX_AGENTS_BYTES:
        raise ValueError('AGENTS.md 不能超过 64 KiB')
    try:
        content = payload.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('AGENTS.md 必须使用 UTF-8 编码') from None
    if not content.strip('\ufeff \t\r\n') or '\x00' in content:
        raise ValueError('AGENTS.md 必须包含有效文本')
    return content

def day_bounds(day: date):
    start = datetime.combine(day, time.min, SHANGHAI).astimezone(timezone.utc)
    return start, start + timedelta(days=1)
