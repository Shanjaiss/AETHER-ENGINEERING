import logging
import re
import sys
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|secret|password|bearer|auth[_-]?token)\b\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"),
    re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
]

class SecretRedactingFormatter(logging.Formatter):
    """Logging formatter that redacts detected secrets and API keys."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        # First pattern has 2 groups: key and value
        redacted = SECRET_PATTERNS[0].sub(r"\1=***REDACTED***", redacted)
        for pattern in SECRET_PATTERNS[1:]:
            redacted = pattern.sub("***REDACTED_SECRET***", redacted)
        return redacted

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging for AETHER ENGINEER."""
    logger = logging.getLogger("aether")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = SecretRedactingFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = setup_logging()
