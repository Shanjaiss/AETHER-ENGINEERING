from config_parser import parse_config
def test_config():
    assert parse_config({'timeout': 30}) == 30
    assert parse_config({}) == 60
