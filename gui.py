from __future__ import annotations

import queue
import tkinter as tk
from dataclasses import replace
from tkinter import messagebox, ttk

from settings import AppSettings, LlmSettings, SttSettings, validate_settings
from ui_tokens import COLORS, FONT, SPACING


class SettingsViewModel:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def build(self, values: dict[str, str]) -> AppSettings:
        result = replace(
            self.settings,
            hotkey=values["hotkey"].strip().lower(),
            record_mode=values["record_mode"],
            stt=SttSettings(
                provider=values["stt_provider"],
                api_base_url=values["stt_url"].strip(),
                api_model=values["stt_model"].strip(),
                local_model=values["local_model"],
                language="tr",
            ),
            llm=LlmSettings(values["llm_url"].strip(), values["llm_model"]),
        )
        return validate_settings(result)


class AppGui:
    FIELD_SPECS = (
        ("Global kısayol", "hotkey", ()),
        ("Kayıt modu", "record_mode", ("toggle", "push_to_talk")),
        ("STT sağlayıcısı", "stt_provider", ("api", "local")),
        ("STT API adresi", "stt_url", ()),
        ("STT API modeli", "stt_model", ()),
        ("Yerel STT modeli", "local_model", ("tiny", "base")),
        ("9Router adresi", "llm_url", ()),
        ("9Router modeli", "llm_model", ("scout-flash", "ulku")),
        ("STT API anahtarı", "stt_key", ()),
        ("9Router API anahtarı", "llm_key", ()),
    )

    def __init__(self, root, settings, settings_store, credentials, controller, events, tray=None):
        self.root, self.store, self.credentials = root, settings_store, credentials
        self.controller, self.events, self.tray = controller, events, tray
        self.vm = SettingsViewModel(settings)
        self.vars = {}
        self.root.title("Ses Yazıcı")
        self.root.configure(bg=COLORS["background"])
        self.root.geometry("620x610")
        self.root.minsize(560, 540)
        self._style()
        self._build(settings)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.after(80, self.poll_events)

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=COLORS["background"], foreground=COLORS["foreground"], fieldbackground=COLORS["card"], font=FONT)
        style.configure("TEntry", bordercolor=COLORS["border"], insertcolor=COLORS["foreground"])
        style.configure("TCombobox", bordercolor=COLORS["border"], arrowsize=14)
        style.configure("Primary.TButton", background=COLORS["primary"], foreground=COLORS["primary_foreground"], padding=(14, 8))
        style.map("Primary.TButton", background=[("active", COLORS["primary"]), ("focus", COLORS["primary"])])
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("Card.TLabel", background=COLORS["card"])

    def _build(self, settings):
        card = ttk.Frame(self.root, style="Card.TFrame", padding=SPACING["xl"])
        card.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])
        ttk.Label(card, text="Ses Yazıcı", style="Card.TLabel", font=("Segoe UI Semibold", 16)).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        defaults = {
            "hotkey": settings.hotkey, "record_mode": settings.record_mode,
            "stt_provider": settings.stt.provider, "stt_url": settings.stt.api_base_url,
            "stt_model": settings.stt.api_model, "local_model": settings.stt.local_model,
            "llm_url": settings.llm.base_url, "llm_model": settings.llm.model,
            "stt_key": "", "llm_key": "",
        }
        for row, (label, name, choices) in enumerate(self.FIELD_SPECS, 1):
            ttk.Label(card, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            var = tk.StringVar(value=defaults[name]); self.vars[name] = var
            if choices:
                widget = ttk.Combobox(card, textvariable=var, values=choices, state="readonly")
            else:
                widget = ttk.Entry(card, textvariable=var, show="*" if name.endswith("_key") else "")
            widget.grid(row=row, column=1, sticky="ew", pady=5)
        card.columnconfigure(1, weight=1)
        self.status_var = tk.StringVar(value="Hazır")
        ttk.Label(card, text="Durum", style="Card.TLabel").grid(row=11, column=0, sticky="w", pady=(14, 5))
        ttk.Label(card, textvariable=self.status_var, style="Card.TLabel").grid(row=11, column=1, sticky="w", pady=(14, 5))
        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=12, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Test Et", command=self.test_action).pack(side="left", padx=5)
        ttk.Button(buttons, text="Kaydet", style="Primary.TButton", command=self.save).pack(side="left")

    def values(self): return {name: var.get() for name, var in self.vars.items()}

    def save(self):
        try:
            for field, key in (("stt_key", "stt_api_key"), ("llm_key", "llm_api_key")):
                value = self.vars[field].get()
                if value:
                    self.credentials.set(key, value)
                    self.vars[field].set("")
            settings = self.vm.build(self.values())
            self.controller.update_settings(settings)
            self.store.save(settings)
            self.vm.settings = settings
            self.status_var.set("Hazır: Ayarlar kaydedildi")
        except Exception as exc:
            messagebox.showerror("Ayar hatası", str(exc))

    def test_action(self):
        if self.controller.state.name == "LISTENING": self.controller.stop_recording()
        else: self.controller.start_recording()

    def poll_events(self):
        try:
            while True: self.status_var.set(self.events.get_nowait().message)
        except queue.Empty: pass
        self.root.after(80, self.poll_events)

    def hide(self):
        if self.tray: self.root.withdraw()
        else: self.exit()

    def show(self): self.root.after(0, self.root.deiconify)
    def exit(self):
        self.controller.shutdown()
        if self.tray: self.tray.stop()
        self.root.after(0, self.root.destroy)
