import hmac
def compare_keys(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
