from validator import is_valid_email
def test_emails():
    assert is_valid_email('user@example.com') is True
    assert is_valid_email('invalid-email') is False
