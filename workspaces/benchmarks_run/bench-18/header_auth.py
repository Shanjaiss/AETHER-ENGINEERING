def extract_token(header_val: str) -> str:
    if header_val.startswith('Bearer '):
        return header_val[7:].strip()
    return ''
