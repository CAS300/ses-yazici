from dataclasses import replace
from pathlib import Path

import httpx
import pytest

import main
from settings import AppSettings, SttSettings


class Credentials:
    def __init__(self, values=None): self.values = values or {}; self.calls = []
    def get(self, name): self.calls.append(name); return self.values.get(name)


@pytest.mark.parametrize("mode,model,cleaner_expected,key_calls", [
    ("combined", "base", True, ["llm_api_key"]),
    ("local_only", "tiny", False, []),
])
def test_a2_a4_a5_build_services_is_always_local(monkeypatch, mode, model, cleaner_expected, key_calls):
    credentials = Credentials({"llm_api_key": "opaque-llm"})
    transcribers = []; cleaners = []
    def fake_transcriber(settings): transcribers.append(settings); return "local-stt"
    def fake_cleaner(base_url, llm_model, key, client):
        cleaners.append((base_url, llm_model, key)); return "cleaner"
    monkeypatch.setattr(main, "build_transcriber", fake_transcriber)
    monkeypatch.setattr(main, "LlmCleaner", fake_cleaner)
    settings = replace(AppSettings(), flow_mode=mode, stt=SttSettings(model, "tr"))
    transcriber, cleaner = main.build_services(settings, credentials, httpx.Client())
    assert transcribers == [settings.stt]
    assert transcriber == "local-stt"
    assert (cleaner is not None) is cleaner_expected
    assert credentials.calls == key_calls
    assert cleaners == ([] if not cleaner_expected else [(settings.llm.base_url, settings.llm.model, "opaque-llm")])


def test_a5_local_only_creates_no_key_or_http_request(monkeypatch):
    requests = []
    client = httpx.Client(transport=httpx.MockTransport(lambda request: requests.append(request)))
    monkeypatch.setattr(main, "build_transcriber", lambda settings: object())
    credentials = Credentials()
    transcriber, cleaner = main.build_services(replace(AppSettings(), flow_mode="local_only"), credentials, client)
    assert transcriber is not None and cleaner is None
    assert credentials.calls == [] and requests == []


def test_combined_requires_only_llm_key(monkeypatch):
    monkeypatch.setattr(main, "build_transcriber", lambda settings: object())
    with pytest.raises(RuntimeError, match="9Router API anahtarı"):
        main.build_services(AppSettings(), Credentials(), httpx.Client())


def test_a11_main_keeps_log_and_dialog_failure_contract():
    source = Path(main.__file__).read_text(encoding="utf-8")
    assert '"error.log"' in source
    assert "messagebox.showerror" in source


def test_main_uses_pynput_and_no_keyboard():
    source = Path(main.__file__).read_text(encoding="utf-8")
    assert "import keyboard" not in source
    assert "PynputKeyboardAdapter" in source

