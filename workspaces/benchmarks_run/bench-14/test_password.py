from password import verify_password
def test_pw():
    assert verify_password('SecurePass1') is True
    assert verify_password('short1') is False
    assert verify_password('NoDigitsHere') is False
