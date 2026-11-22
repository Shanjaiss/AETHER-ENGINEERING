from utils import clean_text
def test_clean():
    assert clean_text('  hello\x00world  ') == 'helloworld'
