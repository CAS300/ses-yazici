import json
from dataclasses import replace

import pytest

from settings import (AppSettings, CredentialStore, LlmSettings, SettingsError,
                      SettingsStore, SttSettings, api_url, validate_base_url,
                      validate_settings)


def test_a1_defaults_modes_models_and_round_trip(tmp_path):
    defaults = AppSettings()
    assert defaults.flow_mode == "combined"
    assert defaults.stt == SttSettings(local_model="base", language="tr")
    path = tmp_path / "config.json"
    store = SettingsStore(path)
    for mode in ("combined", "local_only"):
        for model in ("tiny", "base"):
            expected = replace(defaults, flow_mode=mode, stt=SttSettings(model, "tr"))
            store.save(expected)
            assert store.load() == expected
    assert set(__import__("settings").FLOW_MODES) == {"combined", "local_only"}


@pytest.mark.parametrize("mode", ["api_only", "invalid"])
def test_a1_a6_unsupported_modes_are_sanitized(mode, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"flow_mode": mode}), encoding="utf-8")
    with pytest.raises(SettingsError, match="Ayar dosyası okunamadı veya geçersiz"):
        SettingsStore(path).load()


def test_a6_legacy_stt_api_fields_are_ignored_then_removed(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "flow_mode": "combined",
        "stt": {"provider": "api", "api_base_url": "not-a-url", "api_model": "whisper-1",
                "local_model": "tiny", "language": "tr"},
    }), encoding="utf-8")
    store = SettingsStore(path)
    loaded = store.load()
    assert loaded.stt == SttSettings(local_model="tiny", language="tr")
    store.save(loaded)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["stt"] == {"local_model": "tiny", "language": "tr"}


def test_invalid_json_and_invalid_model_have_domain_error(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(SettingsError): SettingsStore(path).load()
    with pytest.raises(SettingsError, match="tiny veya base"):
        validate_settings(replace(AppSettings(), stt=SttSettings(local_model="large")))


@pytest.mark.parametrize("url,valid", [
    ("https://example.test/v1", True), ("http://localhost:8000/v1", True),
    ("http://127.0.0.1:8000", True), ("http://example.test/v1", False),
    ("https://user:pass@example.test", False),
])
def test_url_policy(url, valid):
    if valid:
        assert validate_base_url(url)
    else:
        with pytest.raises(SettingsError): validate_base_url(url)


def test_url_join_and_llm_validation():
    assert api_url("https://example.test/v1/", "/v1/chat/completions") == "https://example.test/v1/chat/completions"
    with pytest.raises(SettingsError): validate_settings(replace(AppSettings(), llm=LlmSettings(base_url="http://remote.test")))
    assert validate_settings(replace(AppSettings(), flow_mode="local_only", llm=LlmSettings(base_url="http://remote.test")))


class Keys:
    def __init__(self): self.values = {}; self.calls = []
    def get_password(self, service, name): self.calls.append(("get", service, name)); return self.values.get(name)
    def set_password(self, service, name, value): self.calls.append(("set", service, name)); self.values[name] = value
    def delete_password(self, service, name): self.calls.append(("delete", service, name)); self.values.pop(name, None)


def test_a7_credentials_allow_only_llm_key():
    keys = Keys(); store = CredentialStore(keys)
    assert store.ALLOWED == {"llm_api_key"}
    store.set("llm_api_key", "opaque-value")
    assert store.get("llm_api_key") == "opaque-value"
    store.delete("llm_api_key")
    with pytest.raises(ValueError): store.get("stt_api_key")
    with pytest.raises(ValueError): store.set("stt_api_key", "opaque")
    assert [call[2] for call in keys.calls] == ["llm_api_key"] * 3
