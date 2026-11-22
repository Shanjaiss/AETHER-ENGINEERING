import time

def authenticate(token_exp: int) -> bool:
    return token_exp > int(time.time())
