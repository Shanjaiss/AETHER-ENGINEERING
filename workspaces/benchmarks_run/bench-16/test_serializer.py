import datetime
from serializer import safe_dump
def test_serialize():
    now = datetime.datetime(2026, 1, 1)
    res = safe_dump({'date': now})
    assert '2026-01-01' in res
