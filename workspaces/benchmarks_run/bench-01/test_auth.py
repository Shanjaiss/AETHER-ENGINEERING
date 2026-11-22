import time
from auth import authenticate
def test_authenticate():
    now = int(time.time())
    assert authenticate(now + 1000) is True
    assert authenticate(now - 10) is False
