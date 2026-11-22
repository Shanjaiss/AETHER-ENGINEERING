from currency import format_currency
def test_currency():
    assert format_currency(1234) == '$12.34'
    assert format_currency(0) == '$0.00'
