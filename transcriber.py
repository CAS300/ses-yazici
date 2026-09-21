from __future__ import annotations

import os
import tempfile
from typing import Protocol

from settings import SttSettings

class TranscriptionError(RuntimeError):
    pass

class Transcriber(Protocol):
    def transcribe(self, wav_bytes: bytes, *, language: str) -> str: ...

class LocalWhisperTranscriber:
    def __init__(self, model_name: str):
        if model_name not in {"tiny", "base"}:
            raise ValueError("Yerel model tiny veya base olmalıdır.")
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise TranscriptionError(
                    "Yerel STT kurulu değil. requirements-local.txt dosyasını kurun."
                ) from exc
            try:
                self._model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
            except Exception as exc:
                raise TranscriptionError("Yerel STT modeli yüklenemedi.") from exc
        return self._model

    def transcribe(self, wav_bytes: bytes, *, language: str) -> str:
        if not wav_bytes:
            raise TranscriptionError("Ses verisi boş.")
        path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
                handle.write(wav_bytes)
                path = handle.name
            segments, _ = self._load().transcribe(path, language=language)
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError("Yerel transkripsiyon başarısız.") from exc
        finally:
            if path:
                try:
                    os.unlink(path)
                except FileNotFoundError:
                    pass
        if not text:
            raise TranscriptionError("Transkripsiyon boş döndü.")
        return text

def build_transcriber(settings: SttSettings) -> Transcriber:
    return LocalWhisperTranscriber(settings.local_model)
