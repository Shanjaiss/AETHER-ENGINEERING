from profile import calculate_completion
def test_profile():
    assert calculate_completion({'name': 'Alice', 'email': 'a@b.com'}) == 100
    assert calculate_completion({'name': 'Alice'}) == 50
