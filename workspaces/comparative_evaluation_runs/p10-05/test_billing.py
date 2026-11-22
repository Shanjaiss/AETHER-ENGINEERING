from billing import parse_price
from invoice import get_total
def test_pricing():
    assert parse_price(' $19.99 ') == 19.99
    assert get_total(' $50.00 ') == 50.0
