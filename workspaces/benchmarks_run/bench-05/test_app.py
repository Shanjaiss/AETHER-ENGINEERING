from app import get_status
def test_status():
    res = get_status()
    assert res['status'] == 'healthy'
    assert 'version' in res
