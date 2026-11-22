from reducer import counter_reducer
def test_pure():
    initial = {'count': 0}
    next_state = counter_reducer(initial, {'amount': 2})
    assert next_state['count'] == 2
    # Test immutability: initial dictionary was not modified
    assert initial['count'] == 0
