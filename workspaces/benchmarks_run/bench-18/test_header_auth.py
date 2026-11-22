from header_auth import extract_token
def test_extract():
    assert extract_token('Bearer my_token_123') == 'my_token_123'
    assert extract_token('invalid') == ''
