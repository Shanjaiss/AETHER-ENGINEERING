def clean_text(s: str) -> str:
    return s.strip().replace('\x00', '')
