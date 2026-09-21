import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import transcriber
from settings import SttSettings
from transcriber import LocalWhisperTranscriber, TranscriptionError, build_transcriber


def test_a2_api_surface_and_dependencies_are_removed():
    source = Path(transcriber.__file__).read_text(encoding="utf-8")
    assert not hasattr(transcriber, "ApiWhisperTranscriber")
    assert "httpx" not in source
    assert "CredentialStore" not in source
    assert "stt_api_key" not in source


def test_a2_factory_is_local_for_each_model():
    for model in ("tiny", "base"):
        built = build_transcriber(SttSettings(local_model=model))
        assert isinstance(built, LocalWhisperTranscriber)
        assert built.model_name == model


def test_local_is_lazy_joins_segments_and_removes_temp(monkeypatch):
    calls = []
    paths = []
    class Model:
        def __init__(self, name, **kw): calls.append((name, kw))
        def transcribe(self, path, language):
            paths.append(path)
            assert Path(path).exists()
            return ([SimpleNamespace(text=" Merhaba "), SimpleNamespace(text="dünya")], {})
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=Model))
    local = LocalWhisperTranscriber("tiny")
    assert calls == []
    assert local.transcribe(b"RIFF", language="tr") == "Merhaba dünya"
    assert calls == [("tiny", {"device": "cpu", "compute_type": "int8"})]
    assert paths and not Path(paths[0]).exists()


def test_missing_local_extra_is_clear(monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    with pytest.raises(TranscriptionError, match="requirements-local"):
        LocalWhisperTranscriber("base").transcribe(b"RIFF", language="tr")


@pytest.mark.parametrize("model", ["small", "large"])
def test_factory_rejects_non_v2_models(model):
    with pytest.raises(ValueError, match="tiny veya base"):
        build_transcriber(SttSettings(local_model=model))
