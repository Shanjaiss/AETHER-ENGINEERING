def counter_reducer(state: dict, action: dict) -> dict:
    new_state = state.copy()
    new_state['count'] += action.get('amount', 1)
    return new_state
