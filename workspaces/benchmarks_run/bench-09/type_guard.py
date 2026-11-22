def handle_event(event: dict) -> str:
    return event.get('kind', 'unknown')
