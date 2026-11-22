from security import compare_keys
def test_keys():
    assert compare_keys('key123', 'key123') is True
    assert compare_keys('key123', 'key456') is False
