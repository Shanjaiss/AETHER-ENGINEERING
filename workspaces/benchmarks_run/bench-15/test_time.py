from time_helper import get_utc_timestamp
def test_ts():
    dt = get_utc_timestamp()
    assert dt.tzinfo is not None
