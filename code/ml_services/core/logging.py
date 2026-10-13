import logging

_ROOT = "ml_services"
_configured = False


def configure_logging(level: str = "INFO") -> None:
    global _configured
    root = logging.getLogger(_ROOT)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not _configured and not root.handlers:
        root.addHandler(logging.NullHandler())
    _configured = True


def get_logger(name: str) -> logging.Logger:
    if not name.startswith(_ROOT):
        name = f"{_ROOT}.{name}"
    return logging.getLogger(name)
