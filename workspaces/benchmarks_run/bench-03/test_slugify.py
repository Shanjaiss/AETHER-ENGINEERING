from slug import slugify
def test_slugify_spaces():
    assert slugify('Hello World') == 'hello-world'
def test_slugify_special_chars():
    assert slugify('Foo & Bar!!') == 'foo-bar'
