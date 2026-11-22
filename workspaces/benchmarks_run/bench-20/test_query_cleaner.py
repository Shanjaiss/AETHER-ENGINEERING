from query_cleaner import clean_params
def test_clean():
    res = clean_params({'q': 'search', 'page': None, 'filter': ''})
    assert res == {'q': 'search'}
