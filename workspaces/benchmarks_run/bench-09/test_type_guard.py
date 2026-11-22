from type_guard import handle_event
def test_event():
    assert handle_event({'kind': 'click', 'x': 10}) == 'click'
