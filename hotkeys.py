from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app_logger import get_logger
from settings import ALLOWED_HOTKEYS, SettingsError, normalize_hotkey

logger = get_logger("hotkeys")


class HotkeyError(RuntimeError):
    pass


def hotkey_to_pynput(hotkey: str) -> str:
    """Kullanıcı dostu kısayolu pynput HotKey.parse formatına çevirir."""
    parts = hotkey.split("+")
    parsed_parts = []
    for part in parts:
        p = part.strip().lower()
        if len(p) > 1 or p in {"ctrl", "alt", "shift", "space"}:
            parsed_parts.append(f"<{p}>")
        else:
            parsed_parts.append(p)
    return "+".join(parsed_parts)


class HotkeyService:
    def __init__(self, listener_factory: Callable[..., Any] | None = None, backend: Any = None):
        if listener_factory is None and backend is not None:
            listener_factory = backend
        if listener_factory is None:
            def default_factory(on_press, on_release):
                from pynput.keyboard import Listener
                return Listener(on_press=on_press, on_release=on_release)
            listener_factory = default_factory
        self._listener_factory = listener_factory
        self._listener = None
        self._registration = None
        self._active = False

    def register(
        self,
        hotkey: str,
        mode: str,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        try:
            canonical_hotkey = normalize_hotkey(hotkey)
        except SettingsError as exc:
            raise HotkeyError(f"Geçersiz kısayol: {hotkey}") from exc

        if mode not in {"toggle", "push_to_talk"}:
            raise HotkeyError(f"Geçersiz kayıt modu: {mode}")

        from pynput.keyboard import HotKey
        pynput_format = hotkey_to_pynput(canonical_hotkey)
        try:
            parsed_keys = HotKey.parse(pynput_format)
            target_keys = set(parsed_keys)
        except Exception as exc:
            raise HotkeyError(f"Kısayol tuşları ayrıştırılamadı: {hotkey}") from exc

        old_listener = self._listener
        old_reg = self._registration
        old_active = self._active

        def on_activate():
            if mode == "toggle":
                if not self._active:
                    try:
                        logger.debug("Hotkey tetiklendi (toggle -> on_start)")
                        on_start()
                        self._active = True
                    except Exception as exc:
                        logger.exception("on_start callback hatası: %s", exc)
                else:
                    try:
                        logger.debug("Hotkey tetiklendi (toggle -> on_stop)")
                        on_stop()
                        self._active = False
                    except Exception as exc:
                        logger.exception("on_stop callback hatası: %s", exc)
            else:  # push_to_talk
                if not self._active:
                    try:
                        logger.debug("Hotkey tetiklendi (PTT -> on_start)")
                        on_start()
                        self._active = True
                    except Exception as exc:
                        logger.exception("on_start callback hatası: %s", exc)

        hotkey_obj = HotKey(parsed_keys, on_activate)
        current_listener = None

        def _canonical(key):
            if current_listener is not None and hasattr(current_listener, "canonical"):
                try:
                    return current_listener.canonical(key)
                except Exception:
                    return key
            return key

        def _on_press(key):
            c_key = _canonical(key)
            hotkey_obj.press(c_key)

        def _on_release(key):
            c_key = _canonical(key)
            hotkey_obj.release(c_key)
            if mode == "push_to_talk" and self._active:
                if c_key in target_keys or key in target_keys:
                    try:
                        logger.debug("Hotkey tuşu bırakıldı (PTT -> on_stop)")
                        on_stop()
                    except Exception as exc:
                        logger.exception("on_stop callback hatası: %s", exc)
                    finally:
                        self._active = False

        try:
            new_listener = self._listener_factory(_on_press, _on_release)
            current_listener = new_listener
            new_listener.start()
        except Exception as exc:
            self._listener = old_listener
            self._registration = old_reg
            self._active = old_active
            raise HotkeyError(f"Global kısayol kaydedilemedi: {exc}") from exc

        if old_listener is not None:
            try:
                old_listener.stop()
            except Exception:
                pass

        self._listener = new_listener
        self._registration = (canonical_hotkey, mode, on_start, on_stop)
        self._active = False
        logger.info("Hotkey kaydedildi: %s (%s)", canonical_hotkey, mode)

    def unregister(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
        self._listener = None
        self._registration = None
        self._active = False
        logger.info("Hotkey dinleyicisi kaldırıldı.")
