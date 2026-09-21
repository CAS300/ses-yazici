from __future__ import annotations

import io
import threading
import wave
from dataclasses import dataclass


class AudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class AudioClip:
    pcm_s16le: bytes
    sample_rate: int
    channels: int


def encode_wav(clip: AudioClip) -> bytes:
    if clip.sample_rate <= 0 or clip.channels <= 0:
        raise AudioError("Geçersiz ses metadatası.")
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(clip.channels)
        wav.setsampwidth(2)
        wav.setframerate(clip.sample_rate)
        wav.writeframes(clip.pcm_s16le)
    return output.getvalue()


class AudioRecorder:
    def __init__(self, stream_factory=None, *, max_record_seconds: int = 120):
        self._stream_factory = stream_factory
        self._max_seconds = max_record_seconds
        self._stream = None
        self._frames: list[bytes] = []
        self._sample_rate = 16_000
        self._channels = 1
        self._max_bytes = 0
        self._lock = threading.Lock()
        self._recording = False

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    def start(self, *, sample_rate: int = 16_000, channels: int = 1) -> None:
        if sample_rate != 16_000 or channels != 1:
            raise AudioError("Kayıt mono 16 kHz olmalıdır.")
        with self._lock:
            if self._recording:
                raise AudioError("Kayıt zaten sürüyor.")
            self._frames = []
            self._sample_rate = sample_rate
            self._channels = channels
            self._max_bytes = sample_rate * channels * 2 * self._max_seconds
            self._recording = True
        factory = self._stream_factory
        if factory is None:
            try:
                import sounddevice
                factory = sounddevice.InputStream
            except ImportError as exc:
                with self._lock:
                    self._recording = False
                raise AudioError("Ses sürücüsü kurulamadı.") from exc
        try:
            self._stream = factory(samplerate=sample_rate, channels=channels, dtype="int16", callback=self._callback)
            self._stream.start()
        except Exception as exc:
            with self._lock:
                self._recording = False
            self._close_stream()
            raise AudioError("Mikrofon başlatılamadı.") from exc

    def _callback(self, indata, frames, time_info, status) -> None:
        chunk = bytes(indata)
        with self._lock:
            if not self._recording:
                return
            used = sum(map(len, self._frames))
            remaining = self._max_bytes - used
            if remaining > 0:
                self._frames.append(chunk[:remaining])
            if len(chunk) >= remaining:
                self._recording = False

    def stop(self) -> AudioClip:
        with self._lock:
            if not self._recording and not self._frames:
                raise AudioError("Aktif kayıt yok.")
            self._recording = False
            data = b"".join(self._frames)
            self._frames = []
        self._close_stream()
        return AudioClip(data, self._sample_rate, self._channels)

    def cancel(self) -> None:
        with self._lock:
            self._recording = False
            self._frames = []
        self._close_stream()

    def _close_stream(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()
