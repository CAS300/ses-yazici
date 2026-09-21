from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

from audio_recorder import encode_wav
from app_logger import get_logger
from settings import AppSettings

logger = get_logger("controller")


class AppState(Enum):
    READY = auto()
    LISTENING = auto()
    TRANSCRIBING = auto()
    CLEANING = auto()
    INJECTING = auto()
    WRITTEN = auto()
    ERROR = auto()


@dataclass(frozen=True)
class StatusEvent:
    state: AppState
    message: str


STATUS_TEXT = {
    AppState.READY: "Hazır",
    AppState.LISTENING: "Dinleniyor...",
    AppState.TRANSCRIBING: "Düzenleniyor",
    AppState.CLEANING: "Düzenleniyor",
    AppState.INJECTING: "Düzenleniyor",
    AppState.WRITTEN: "Yazıldı",
    AppState.ERROR: "Hata",
}


class AppController:
    def __init__(self, recorder, transcriber, cleaner, injector, settings: AppSettings, *,
                 events=None, hotkeys=None, rebuild_services: Callable | None = None,
                 resources=(), thread_factory=threading.Thread):
        self.recorder = recorder
        self.transcriber = transcriber
        self.cleaner = cleaner
        self.injector = injector
        self.settings = settings
        self.events = events or queue.Queue()
        self.hotkeys = hotkeys
        self.rebuild_services = rebuild_services
        self.resources = list(resources)
        self.thread_factory = thread_factory
        self._lock = threading.Lock()
        self._state = AppState.READY
        self._worker = None
        self._shutdown = False
        self._emit(AppState.READY)

    @property
    def state(self):
        with self._lock:
            return self._state

    def _emit(self, state: AppState, detail: str = ""):
        with self._lock:
            self._state = state
        message = STATUS_TEXT[state] + (f": {detail}" if detail else "")
        logger.debug("Durum geçişi: %s (%s)", state.name, message)
        self.events.put(StatusEvent(state, message))

    def start_recording(self) -> None:
        with self._lock:
            if self._shutdown or self._state != AppState.READY:
                return
            self._state = AppState.LISTENING
        logger.info("Kayıt başlatılıyor.")
        try:
            self.recorder.start(sample_rate=self.settings.sample_rate, channels=1)
        except Exception as exc:
            logger.exception("Mikrofon başlatılamadı: %s", exc)
            self._emit(AppState.ERROR, "Mikrofon başlatılamadı")
            return
        self.events.put(StatusEvent(AppState.LISTENING, STATUS_TEXT[AppState.LISTENING]))

    def stop_recording(self) -> None:
        with self._lock:
            if self._shutdown or self._state != AppState.LISTENING:
                return
            self._state = AppState.TRANSCRIBING
        logger.info("Kayıt durduruldu, pipeline iş parçacığı başlatılıyor.")
        self.events.put(StatusEvent(AppState.TRANSCRIBING, STATUS_TEXT[AppState.TRANSCRIBING]))
        self._worker = self.thread_factory(target=self._pipeline, name="dictation-worker", daemon=True)
        self._worker.start()

    def _pipeline(self):
        try:
            logger.info("Pipeline işleme başladı.")
            clip = self.recorder.stop()
            wav_bytes = encode_wav(clip)
            raw = self.transcriber.transcribe(wav_bytes, language=self.settings.stt.language)
            if not raw.strip():
                raise RuntimeError("Transkripsiyon boş")
            output = raw
            if self.settings.flow_mode != "local_only":
                if self.cleaner is None:
                    raise RuntimeError("Temizleme servisi hazır değil")
                self._emit(AppState.CLEANING)
                output = self.cleaner.clean(raw)
                if not output.strip():
                    raise RuntimeError("Düzenlenmiş metin boş")
            self._emit(AppState.INJECTING)
            self.injector.paste(output)
            self._emit(AppState.WRITTEN)
            self._emit(AppState.READY)
            logger.info("Pipeline başarıyla tamamlandı.")
        except Exception as exc:
            logger.exception("Pipeline işleminde hata oluştu: %s", exc)
            self._emit(AppState.ERROR, "İşlem tamamlanamadı; ayarları kontrol edin")

    def reset_error(self):
        if self.state == AppState.ERROR:
            self._emit(AppState.READY)

    def update_settings(self, settings: AppSettings) -> None:
        with self._lock:
            if self._state not in {AppState.READY, AppState.ERROR}:
                raise RuntimeError("İşlem sürerken ayarlar değiştirilemez.")
        old_settings = self.settings
        old_services = (self.transcriber, self.cleaner)
        new_services = self.rebuild_services(settings) if self.rebuild_services else old_services
        try:
            if self.hotkeys:
                self.hotkeys.register(settings.hotkey, settings.record_mode, self.start_recording, self.stop_recording)
        except Exception:
            self.transcriber, self.cleaner = old_services
            self.settings = old_settings
            raise
        self.transcriber, self.cleaner = new_services
        self.settings = settings
        self.reset_error()

    def shutdown(self) -> None:
        with self._lock:
            self._shutdown = True
        try:
            self.recorder.cancel()
        finally:
            if self.hotkeys:
                self.hotkeys.unregister()
            worker = self._worker
            if worker and worker.is_alive() and worker is not threading.current_thread():
                worker.join(timeout=3)
            for resource in self.resources:
                close = getattr(resource, "close", None) or getattr(resource, "stop", None)
                if close:
                    try:
                        close()
                    except Exception:
                        pass
