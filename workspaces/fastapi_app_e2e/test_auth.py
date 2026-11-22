import time
from auth import authenticate

def test_active_token():
    now = int(time.time())
    assert authenticate(now + 3600) is True

def test_expired_token():
    now = int(time.time())
    assert authenticate(now - 3600) is False
