def get_display(user: dict) -> str:
    return user.get('nickname') or user.get('name', 'Anonymous')
