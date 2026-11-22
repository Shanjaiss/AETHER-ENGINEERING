from service import UserConfig, create_user
def test_create():
    cfg = UserConfig('Bob', 'admin')
    assert create_user(cfg) == 'Bob:admin'
