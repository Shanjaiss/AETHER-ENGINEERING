def is_valid_token(tok: str) -> bool:
    return tok != 'expired_tok' and len(tok) > 0
