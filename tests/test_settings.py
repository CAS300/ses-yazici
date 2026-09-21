import json
from dataclasses import replace

import pytest

from settings import (AppSettings, CredentialStore, LlmSettings, SettingsError,
                      SettingsStore, SttSettings, api_url, validate_base_url,
                      validate_settings)


def test_defaults_and_atomic_round_trip_without_secrets(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    calls = []
    monkeypatch.setattr("settings.os.replace", lambda a, b: (calls.append((a, b)), __import__("os").rename(a, b))[1])
    store = SettingsStore(path); store.save(AppSettings())
    assert calls and store.load() == AppSettings()
    raw = path.read_text()
    assert "api_key" not in raw and "secret" not in raw


def test_invalid_json_has_domain_error(tmp_path):
    path = tmp_path / "config.json"; path.write_text("{")
    with pytest.raises(SettingsError): SettingsStore(path).load()


@pytest.mark.parametrize("url,valid", [
    ("https://example.test/v1", True), ("http://localhost:8000/v1", True),
    ("http://127.0.0.1:8000", True), ("http://example.test/v1", False),
    ("https://user:pass@example.test", False),
])
def test_url_policy(url, valid):
    if valid: assert validate_base_url(url)
    else:
        with pytest.raises(SettingsError): validate_base_url(url)


def test_url_join_avoids_double_v1():
    assert api_url("https://example.test/v1/", "/v1/chat/completions") == "https://example.test/v1/chat/completions"


def test_validation_choices():
    with pytest.raises(SettingsError): validate_settings(replace(AppSettings(), sample_rate=44_100))
    with pytest.raises(SettingsError): validate_settings(replace(AppSettings(), llm=LlmSettings(model="bad")))


class Keys:
    def __init__(self): self.values = {}; self.calls = []
    def get_password(self, service, name): self.calls.append(("get", service, name)); return self.values.get(name)
    def set_password(self, service, name, value): self.calls.append(("set", service, name)); self.values[name] = value
    def delete_password(self, service, name): self.calls.append(("delete", service, name)); self.values.pop(name, None)


def test_credentials_use_keyring_adapter():
    keys = Keys(); store = CredentialStore(keys)
    store.set("stt_api_key", "opaque-value")
    assert store.get("stt_api_key") == "opaque-value"
    store.delete("stt_api_key")
    assert [c[0] for c in keys.calls] == ["set", "get", "delete"]
