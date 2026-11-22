from rate_limiter import get_remaining
def test_remaining():
    assert get_remaining(5, 10) == 5
    assert get_remaining(15, 10) == 0
