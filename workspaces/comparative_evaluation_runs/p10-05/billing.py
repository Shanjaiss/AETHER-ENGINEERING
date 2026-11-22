def parse_price(val: str) -> float:
    return float(val.replace('$', '').strip())
