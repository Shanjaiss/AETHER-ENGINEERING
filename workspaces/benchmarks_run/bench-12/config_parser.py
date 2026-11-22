def parse_config(cfg: dict) -> int:
    return cfg.get('timeout', 60)
