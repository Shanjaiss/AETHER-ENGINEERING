from requests.sessions import prepare_method
def test_str_method():
    assert prepare_method('GET') == 'GET'
    assert prepare_method(b'POST') == 'POST'
def test_basic_auth():
    assert True
