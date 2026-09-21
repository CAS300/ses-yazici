import sys
from types import SimpleNamespace

import httpx
import pytest

from settings import CredentialStore, SttSettings
from transcriber import (ApiWhisperTranscriber, LocalWhisperTranscriber,
                         TranscriptionError, build_transcriber)


def test_api_multipart_contract_and_parse():
    captured = {}
    def handler(request):
        captured["request"] = request
        return httpx.Response(200, json={"text": " merhaba   dünya "})
    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = ApiWhisperTranscriber("https://stt.test/v1", "whisper-1", "opaque", client).transcribe(b"RIFFdata", language="tr")
    request = captured["request"]; body = request.content
    assert str(request.url) == "https://stt.test/v1/audio/transcriptions"
    assert request.headers["authorization"].startswith("Bearer ")
    assert b'name="model"' in body and b"whisper-1" in body
    assert b'name="language"' in body and b"tr" in body
    assert b'filename="recording.wav"' in body and b"audio/wav" in body
    assert result == "merhaba dünya"


def test_api_error_is_domain_error():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    with pytest.raises(TranscriptionError): ApiWhisperTranscriber("https://x.test/v1", "m", "k", client).transcribe(b"x", language="tr")


def test_local_is_lazy_and_joins_segments(monkeypatch):
    calls = []
    class Model:
        def __init__(self, name, **kw): calls.append(name)
        def transcribe(self, path, language): return ([SimpleNamespace(text=" Merhaba "), SimpleNamespace(text="dünya")], {})
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=Model))
    local = LocalWhisperTranscriber("tiny")
    assert calls == []
    assert local.transcribe(b"RIFF", language="tr") == "Merhaba dünya"
    assert calls == ["tiny"]


def test_missing_local_extra_is_clear(monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    with pytest.raises(TranscriptionError, match="requirements-local"):
        LocalWhisperTranscriber("base").transcribe(b"RIFF", language="tr")


def test_factory_local_requires_no_key():
    assert isinstance(build_transcriber(SttSettings(provider="local"), object()), LocalWhisperTranscriber)
