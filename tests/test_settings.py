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


def test_flow_mode_defaults_and_round_trip(tmp_path):
    settings = AppSettings()
    assert settings.flow_mode == "combined"
    assert settings.stt.local_model == "base"
    path = tmp_path / "config.json"
    store = SettingsStore(path)
    for mode in ("combined", "local_only", "api_only"):
        expected = replace(settings, flow_mode=mode)
        store.save(expected)
        assert store.load() == expected
        assert json.loads(path.read_text(encoding="utf-8"))["flow_mode"] == mode


def test_legacy_config_without_flow_mode_uses_combined(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"hotkey": "f9"}), encoding="utf-8")
    assert SettingsStore(path).load().flow_mode == "combined"


def test_invalid_flow_mode_is_rejected():
    with pytest.raises(SettingsError, match="Çalışma modu"):
        validate_settings(replace(AppSettings(), flow_mode="invalid"))


@pytest.mark.parametrize("mode,invalid_stt,invalid_llm,valid", [
    ("local_only", True, True, True),
    ("combined", True, False, True),
    ("combined", False, True, False),
    ("api_only", True, False, False),
    ("api_only", False, True, False),
    ("api_only", False, False, True),
])
def test_url_validation_depends_on_flow_mode(mode, invalid_stt, invalid_llm, valid):
    settings = replace(
        AppSettings(),
        flow_mode=mode,
        stt=replace(AppSettings().stt, api_base_url="http://remote.test" if invalid_stt else "https://stt.test"),
        llm=replace(AppSettings().llm, base_url="http://remote.test" if invalid_llm else "https://llm.test"),
    )
    if valid:
        assert validate_settings(settings) == settings
    else:
        with pytest.raises(SettingsError):
            validate_settings(settings)


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
