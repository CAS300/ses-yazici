from __future__ import annotations

import time
from typing import Protocol


class InjectionError(RuntimeError):
    pass


class ClipboardPort(Protocol):
    def paste(self) -> str: ...
    def copy(self, text: str) -> None: ...


class KeyboardPort(Protocol):
    def send(self, hotkey: str) -> None: ...


class TextInjector:
    def __init__(self, clipboard: ClipboardPort, keyboard: KeyboardPort, *, sleep=time.sleep, delay=0.08):
        self.clipboard = clipboard
        self.keyboard = keyboard
        self.sleep = sleep
        self.delay = delay

    def paste(self, text: str, *, restore_clipboard: bool = True) -> None:
        if not text.strip():
            raise InjectionError("Boş metin yapıştırılamaz.")
        try:
            previous = self.clipboard.paste()
        except Exception:
            previous = None
        injected = text
        try:
            self.clipboard.copy(injected)
            self.keyboard.send("ctrl+v")
            self.sleep(self.delay)
        except Exception as exc:
            raise InjectionError("Metin odaklı alana yapıştırılamadı.") from exc
        finally:
            if restore_clipboard and previous is not None:
                try:
                    if self.clipboard.paste() == injected:
                        self.clipboard.copy(previous)
                except Exception:
                    pass
