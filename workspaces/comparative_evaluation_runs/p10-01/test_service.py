import service
def test_login():
    assert service.login_user('valid_tok') is True
    assert service.login_user('expired_tok') is False
