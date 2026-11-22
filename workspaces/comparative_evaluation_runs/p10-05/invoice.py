def get_total(val: str) -> float:
    return float(val.replace('$', '').strip())
