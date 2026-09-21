from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class SttSettings:
    provider: Literal["api", "local"] = "api"
    api_base_url: str = "https://api.openai.com/v1"
    api_model: str = "whisper-1"
    local_model: Literal["tiny", "base"] = "tiny"
    language: str = "tr"


@dataclass(frozen=True)
class LlmSettings:
    base_url: str = "https://router.erensahin.tr/v1"
    model: Literal["scout-flash", "ulku"] = "scout-flash"


@dataclass(frozen=True)
class AppSettings:
    hotkey: str = "f8"
    record_mode: Literal["toggle", "push_to_talk"] = "toggle"
    stt: SttSettings = field(default_factory=SttSettings)
    llm: LlmSettings = field(default_factory=LlmSettings)
    sample_rate: int = 16_000
    max_record_seconds: int = 120


def validate_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise SettingsError("Uzak servis adresi HTTPS kullanmalıdır.")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SettingsError("Servis adresi geçersiz.")
    return value


def api_url(base_url: str, path: str) -> str:
    base = validate_base_url(base_url)
    suffix = path.lstrip("/")
    if base.endswith("/v1") and suffix.startswith("v1/"):
        suffix = suffix[3:]
    return f"{base}/{suffix}"


def validate_settings(settings: AppSettings) -> AppSettings:
    if not settings.hotkey.strip():
        raise SettingsError("Kısayol boş olamaz.")
    if settings.record_mode not in {"toggle", "push_to_talk"}:
        raise SettingsError("Kayıt modu geçersiz.")
    if settings.stt.provider not in {"api", "local"}:
        raise SettingsError("STT sağlayıcısı geçersiz.")
    if settings.stt.local_model not in {"tiny", "base"}:
        raise SettingsError("Yerel model tiny veya base olmalıdır.")
    if settings.llm.model not in {"scout-flash", "ulku"}:
        raise SettingsError("LLM modeli geçersiz.")
    if settings.sample_rate != 16_000:
        raise SettingsError("MVP örnekleme hızı 16000 olmalıdır.")
    if not 1 <= settings.max_record_seconds <= 600:
        raise SettingsError("Maksimum kayıt süresi 1-600 saniye olmalıdır.")
    if settings.stt.provider == "api":
        validate_base_url(settings.stt.api_base_url)
    validate_base_url(settings.llm.base_url)
    return settings


class SettingsStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            result = AppSettings(
                hotkey=data.get("hotkey", "f8"),
                record_mode=data.get("record_mode", "toggle"),
                stt=SttSettings(**data.get("stt", {})),
                llm=LlmSettings(**data.get("llm", {})),
                sample_rate=data.get("sample_rate", 16_000),
                max_record_seconds=data.get("max_record_seconds", 120),
            )
            return validate_settings(result)
        except (OSError, json.JSONDecodeError, TypeError, SettingsError) as exc:
            raise SettingsError("Ayar dosyası okunamadı veya geçersiz.") from exc

    def save(self, settings: AppSettings) -> None:
        validate_settings(settings)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        payload = json.dumps(asdict(settings), ensure_ascii=False, indent=2)
        try:
            temporary.write_text(payload + "\n", encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            finally:
                raise SettingsError("Ayarlar güvenli biçimde kaydedilemedi.") from exc


class CredentialStore:
    SERVICE = "ses-yazici"
    ALLOWED = {"stt_api_key", "llm_api_key"}

    def __init__(self, backend=None):
        if backend is None:
            import keyring
            backend = keyring
        self.backend = backend

    def _check(self, name: str) -> None:
        if name not in self.ALLOWED:
            raise ValueError("Bilinmeyen credential adı.")

    def get(self, name: Literal["stt_api_key", "llm_api_key"]) -> str | None:
        self._check(name)
        return self.backend.get_password(self.SERVICE, name)

    def set(self, name: Literal["stt_api_key", "llm_api_key"], value: str) -> None:
        self._check(name)
        if not value:
            self.delete(name)
            return
        self.backend.set_password(self.SERVICE, name, value)

    def delete(self, name: Literal["stt_api_key", "llm_api_key"]) -> None:
        self._check(name)
        try:
            self.backend.delete_password(self.SERVICE, name)
        except Exception as exc:
            if exc.__class__.__name__ != "PasswordDeleteError":
                raise
