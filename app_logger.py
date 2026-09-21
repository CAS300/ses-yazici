from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import sys

FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"

_SECRET_PATTERNS = [
    (re.compile(r"(Bearer\s+)[^\s\"',]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"((?:api[_-]?key|secret|token|password)\s*[:=]\s*)[^\s\"',]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"sk-[a-zA-Z0-9_-]{8,}", re.IGNORECASE), "[REDACTED]"),
]


def redact_secrets(text: str) -> str:
    """Metin içindeki hassas API anahtarı ve yetkilendirme bilgilerini maskeler."""
    if not isinstance(text, str):
        return text
    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class SecretFilter(logging.Filter):
    """Log kayıtlarındaki gizli anahtarları ve tokenları filtreleyen logging filtresi."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_secrets(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: redact_secrets(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
                elif isinstance(record.args, tuple):
                    record.args = tuple(redact_secrets(str(v)) if isinstance(v, str) else v for v in record.args)
        except Exception:
            pass
        return True


def get_log_path() -> Path:
    """Varsayılan log dosya yolunu döndürür."""
    env_path = os.environ.get("SES_YAZICI_LOG_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent / "app.log"


def setup_logging(log_path: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """Uygulama genelinde RotatingFileHandler ile yapılandırılmış loglamayı başlatır."""
    path = Path(log_path) if log_path else get_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Gürültülü 3. parti kütüphanelerin loglarını sustur (yalnızca WARN ve ERROR göster)
    noisy_modules = ["PIL", "httpcore", "httpx", "keyring", "urllib3", "faster_whisper", "ctranslate2"]
    for mod in noisy_modules:
        logging.getLogger(mod).setLevel(logging.WARNING)

    # Varsa eski RotatingFileHandler'ları temizle
    for h in list(root_logger.handlers):
        if isinstance(h, RotatingFileHandler):
            root_logger.removeHandler(h)
            h.close()

    file_handler = RotatingFileHandler(
        filename=str(path),
        maxBytes=1 * 1024 * 1024,  # 1 MB sınır
        backupCount=2,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(FORMAT))
    file_handler.addFilter(SecretFilter())
    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Verilen modül için logger döndürür."""
    return logging.getLogger(name)


def open_log_file(log_path: Path | None = None) -> None:
    """Log dosyasını sistemin varsayılan editörüyle açar."""
    path = Path(log_path) if log_path else get_log_path()
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

        if hasattr(os, "startfile"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(path)])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        logging.getLogger(__name__).warning("Log dosyası açılamadı: %s", exc)
