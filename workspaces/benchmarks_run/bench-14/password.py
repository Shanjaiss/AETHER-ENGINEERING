def verify_password(pw: str) -> bool:
    return len(pw) >= 8 and any(c.isdigit() for c in pw)
