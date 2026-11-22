import auth
def login_user(tok: str) -> bool:
    return auth.is_valid_token(tok)
