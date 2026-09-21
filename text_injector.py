from __future__ import annotations

import time
from typing import Any, Protocol

from app_logger import get_logger

logger = get_logger("text_injector")


class InjectionError(RuntimeError):
    pass


class ClipboardPort(Protocol):
    def paste(self) -> str: ...
    def copy(self, text: str) -> None: ...


class KeyboardPort(Protocol):
    def send(self, hotkey: str) -> None: ...


class PynputKeyboardAdapter:
    """pynput Controller kullanarak tuş simülasyonu sağlayan adaptör."""

    def __init__(self, controller: Any = None):
        if controller is None:
            from pynput.keyboard import Controller
            controller = Controller()
        self.controller = controller

    def send(self, hotkey: str) -> None:
        if hotkey.lower() in {"ctrl+v", "^v"}:
            from pynput.keyboard import Key
            logger.debug("pynput ile ctrl+v tuş kombinasyonu simüle ediliyor")
            self.controller.press(Key.ctrl)
            self.controller.press("v")
            self.controller.release("v")
            self.controller.release(Key.ctrl)


class TextInjector:
    def __init__(self, clipboard: ClipboardPort, keyboard: KeyboardPort, *, sleep=time.sleep, delay=0.08):
        self.clipboard = clipboard
        self.keyboard = keyboard
        self.sleep = sleep
        self.delay = delay

    def paste(self, text: str, *, restore_clipboard: bool = True) -> None:
        if not text.strip():
            logger.warning("Yapıştırılacak metin boş.")
            raise InjectionError("Boş metin yapıştırılamaz.")
        try:
            previous = self.clipboard.paste()
        except Exception:
            previous = None
        injected = text
        try:
            logger.debug("Metin panoya kopyalanıyor (uzunluk: %d karakter)", len(injected))
            self.clipboard.copy(injected)
            self.keyboard.send("ctrl+v")
            self.sleep(self.delay)
            logger.info("Metin başarıyla yapıştırıldı.")
        except Exception as exc:
            logger.exception("Metin odaklı alana yapıştırılamadı: %s", exc)
            raise InjectionError("Metin odaklı alana yapıştırılamadı.") from exc
        finally:
            if restore_clipboard and previous is not None:
                try:
                    if self.clipboard.paste() == injected:
                        self.clipboard.copy(previous)
                        logger.debug("Önceki pano içeriği geri yüklendi.")
                except Exception:
                    pass
