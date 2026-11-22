from display import get_display
def test_display():
    assert get_display({'name': 'John'}) == 'John'
    assert get_display({'name': 'John', 'nickname': 'Johnny'}) == 'Johnny'
