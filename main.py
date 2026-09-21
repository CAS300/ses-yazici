from __future__ import annotations

import queue
from pathlib import Path
import tkinter as tk

import httpx

from audio_recorder import AudioRecorder
from controller import AppController
from gui import AppGui
from hotkeys import HotkeyService
from llm_cleaner import LlmCleaner
from settings import CredentialStore, SettingsStore
from text_injector import TextInjector
from transcriber import build_transcriber


class TrayAdapter:
    def __init__(self, root, controller):
        self.root, self.controller, self.icon = root, controller, None
        self.gui = None

    def start(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            image = Image.new("RGB", (64, 64), "#18181b")
            draw = ImageDraw.Draw(image)
            draw.ellipse((15, 8, 49, 42), fill="#22c55e")
            draw.rectangle((29, 38, 35, 54), fill="#22c55e")
            menu = pystray.Menu(
                pystray.MenuItem("Göster", lambda: self.gui.show()),
                pystray.MenuItem("Kaydı başlat / bitir", self._toggle),
                pystray.MenuItem("Çıkış", lambda: self.gui.exit()),
            )
            self.icon = pystray.Icon("ses-yazici", image, "Ses Yazıcı", menu)
            self.icon.run_detached()
        except Exception:
            self.icon = None

    def _toggle(self):
        if self.controller.state.name == "LISTENING": self.controller.stop_recording()
        else: self.controller.start_recording()

    def stop(self):
        if self.icon: self.icon.stop()


def create_app(config_path: Path | None = None):
    config_path = config_path or Path.home() / ".ses-yazici" / "config.json"
    store = SettingsStore(config_path)
    settings = store.load()
    credentials = CredentialStore()
    client = httpx.Client()
    transcriber = build_transcriber(settings.stt, credentials, client)
    llm_key = credentials.get("llm_api_key")
    if not llm_key:
        raise RuntimeError("9Router API anahtarı Windows Credential Manager'da bulunamadı.")
    cleaner = LlmCleaner(settings.llm.base_url, settings.llm.model, llm_key, client)
    import keyboard
    import pyperclip
    recorder = AudioRecorder(max_record_seconds=settings.max_record_seconds)
    hotkeys = HotkeyService(keyboard)
    injector = TextInjector(pyperclip, keyboard)
    events = queue.Queue()

    def rebuild(new_settings):
        return (
            build_transcriber(new_settings.stt, credentials, client),
            LlmCleaner(new_settings.llm.base_url, new_settings.llm.model,
                       credentials.get("llm_api_key") or "", client),
        )

    controller = AppController(recorder, transcriber, cleaner, injector, settings,
                               events=events, hotkeys=hotkeys,
                               rebuild_services=rebuild, resources=(client,))
    hotkeys.register(settings.hotkey, settings.record_mode,
                     controller.start_recording, controller.stop_recording)
    root = tk.Tk()
    tray = TrayAdapter(root, controller)
    gui = AppGui(root, settings, store, credentials, controller, events, tray)
    tray.gui = gui
    tray.start()
    return root, gui


def main():
    try:
        root, _gui = create_app()
    except Exception as exc:
        root = tk.Tk(); root.withdraw()
        from tkinter import messagebox
        messagebox.showerror("Ses Yazıcı başlatılamadı", str(exc))
        root.destroy()
        return 1
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
