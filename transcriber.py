from __future__ import annotations

import os
import tempfile
from typing import Protocol

import httpx

from settings import CredentialStore, SttSettings, api_url


class TranscriptionError(RuntimeError):
    pass


class Transcriber(Protocol):
    def transcribe(self, wav_bytes: bytes, *, language: str) -> str: ...


class ApiWhisperTranscriber:
    def __init__(self, base_url: str, model: str, api_key: str, client: httpx.Client):
        self.url = api_url(base_url, "v1/audio/transcriptions")
        self.model = model
        self.api_key = api_key
        self.client = client

    def transcribe(self, wav_bytes: bytes, *, language: str) -> str:
        if not wav_bytes:
            raise TranscriptionError("Ses verisi boş.")
        try:
            response = self.client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"model": self.model, "language": language},
                files={"file": ("recording.wav", wav_bytes, "audio/wav")},
                timeout=60.0,
            )
            response.raise_for_status()
            text = response.json().get("text", "")
        except (httpx.HTTPError, ValueError, AttributeError) as exc:
            raise TranscriptionError("Ses yazıya çevrilemedi.") from exc
        if not isinstance(text, str) or not text.strip():
            raise TranscriptionError("Transkripsiyon boş döndü.")
        return " ".join(text.split())


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


def build_transcriber(settings: SttSettings, credentials: CredentialStore, client=None) -> Transcriber:
    if settings.provider == "local":
        return LocalWhisperTranscriber(settings.local_model)
    key = credentials.get("stt_api_key")
    if not key:
        raise TranscriptionError("STT API anahtarı Windows Credential Manager'da bulunamadı.")
    return ApiWhisperTranscriber(settings.api_base_url, settings.api_model, key, client or httpx.Client())
