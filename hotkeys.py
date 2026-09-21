from __future__ import annotations

from collections.abc import Callable

class HotkeyError(RuntimeError):
    pass

class HotkeyService:
    def __init__(self, backend=None):
        if backend is None:
            import keyboard
            backend = keyboard
        self.backend = backend
        self._handles: list[object] = []
        self._pressed = False
        self._active = False
        self._registration = None

    def register(self, hotkey: str, mode: str, on_start: Callable[[], None], on_stop: Callable[[], None]) -> None:
        if not hotkey.strip() or mode not in {"toggle", "push_to_talk"}:
            raise HotkeyError("Kısayol veya kayıt modu geçersiz.")
        old = (self._registration, list(self._handles))
        new_handles = []

        def down(_event=None):
            if self._pressed:
                return
            self._pressed = True
            if mode == "push_to_talk" and self._active:
                return
            callback = on_stop if mode == "toggle" and self._active else on_start
            try:
                callback()
            except Exception:
                # Callback hata verse bile tuş fiziksel olarak bırakılana kadar _pressed True kalmalı
                return
            self._active = not self._active if mode == "toggle" else True

        def up(_event=None):
            if not self._pressed:
                return
            self._pressed = False
            if mode != "push_to_talk" or not self._active:
                return
            try:
                on_stop()
            except Exception:
                return
            self._active = False

        try:
            new_handles.append(self.backend.on_press_key(hotkey, down, suppress=False))
            new_handles.append(self.backend.on_release_key(hotkey, up, suppress=False))
        except Exception as exc:
            for handle in new_handles:
                try:
                    self.backend.unhook(handle)
                except Exception:
                    pass
            self._registration, self._handles = old
            raise HotkeyError("Global kısayol kaydedilemedi.") from exc
        for handle in old[1]:
            self.backend.unhook(handle)
        self._handles = new_handles
        self._registration = (hotkey, mode, on_start, on_stop)
        self._pressed = self._active = False

    def unregister(self) -> None:
        for handle in self._handles:
            try:
                self.backend.unhook(handle)
            except Exception:
                pass
        self._handles = []
        self._registration = None
        self._pressed = self._active = False
