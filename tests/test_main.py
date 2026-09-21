from dataclasses import replace

import httpx
import pytest

import main
from settings import AppSettings


class Credentials:
    def __init__(self, values=None):
        self.values = values or {}
        self.calls = []

    def get(self, name):
        self.calls.append(name)
        return self.values.get(name)


@pytest.mark.parametrize(
    "mode,provider,cleaner_expected,key_calls",
    [
        ("combined", "local", True, ["llm_api_key"]),
        ("local_only", "local", False, []),
        ("api_only", "api", True, ["stt_api_key", "llm_api_key"]),
    ],
)
def test_build_services_selects_mode_and_credentials(monkeypatch, mode, provider, cleaner_expected, key_calls):
    credentials = Credentials({"stt_api_key": "opaque-stt", "llm_api_key": "opaque-llm"})
    transcribers = []
    cleaners = []

    def fake_transcriber(settings, passed_credentials, client):
        transcribers.append(settings.provider)
        if settings.provider == "api":
            assert passed_credentials.get("stt_api_key") == "opaque-stt"
        return f"{settings.provider}-stt"

    def fake_cleaner(base_url, model, key, client):
        cleaners.append((base_url, model, key))
        return "cleaner"

    monkeypatch.setattr(main, "build_transcriber", fake_transcriber)
    monkeypatch.setattr(main, "LlmCleaner", fake_cleaner)
    settings = replace(AppSettings(), flow_mode=mode)
    transcriber, cleaner = main.build_services(settings, credentials, httpx.Client())

    assert transcribers == [provider]
    assert (cleaner is not None) is cleaner_expected
    assert credentials.calls == key_calls
    assert cleaners == ([] if not cleaner_expected else [(settings.llm.base_url, settings.llm.model, "opaque-llm")])
    assert transcriber == f"{provider}-stt"


def test_local_only_creates_no_http_request(monkeypatch):
    requests = []
    client = httpx.Client(transport=httpx.MockTransport(lambda request: requests.append(request)))
    monkeypatch.setattr(main, "build_transcriber", lambda settings, credentials, client: object())
    transcriber, cleaner = main.build_services(
        replace(AppSettings(), flow_mode="local_only"), Credentials(), client
    )
    assert transcriber is not None and cleaner is None
    assert requests == []


@pytest.mark.parametrize(
    "mode,values",
    [("combined", {}), ("api_only", {"stt_api_key": "opaque-stt"})],
)
def test_build_services_requires_used_llm_key(mode, values):
    with pytest.raises(RuntimeError, match="9Router API anahtarı"):
        main.build_services(replace(AppSettings(), flow_mode=mode), Credentials(values), httpx.Client())
