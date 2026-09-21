from __future__ import annotations

import queue
import tkinter as tk
from dataclasses import replace
from tkinter import messagebox, ttk

from app_logger import open_log_file
from controller import AppState
from settings import ALLOWED_HOTKEYS, AppSettings, LlmSettings, SttSettings, validate_settings
from ui_tokens import COLORS, FONT, SPACING

FLOW_MODE_LABELS = {
    "Kombine (Yerel Whisper + 9Router LLM)": "combined",
    "Yalnızca Yerel (Ham / Çevrimdışı)": "local_only",
}
FLOW_MODE_NAMES = {mode: label for label, mode in FLOW_MODE_LABELS.items()}


def key_visibility(current_show: str) -> tuple[str, str]:
    return ("", "Gizle") if current_show == "*" else ("*", "Göster")


class SettingsViewModel:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def build(self, values: dict[str, str]) -> AppSettings:
        result = replace(
            self.settings,
            hotkey=values["hotkey"].strip(),
            record_mode=values["record_mode"],
            flow_mode=FLOW_MODE_LABELS[values["flow_mode"]],
            stt=SttSettings(local_model=values["local_model"], language="tr"),
            llm=LlmSettings(values["llm_url"].strip(), values["llm_model"]),
        )
        return validate_settings(result)


class AppGui:
    FIELD_SPECS = (
        ("Global kısayol", "hotkey", ALLOWED_HOTKEYS),
        ("Kayıt modu", "record_mode", ("toggle", "push_to_talk")),
        ("Çalışma modu", "flow_mode", tuple(FLOW_MODE_LABELS)),
        ("Yerel STT modeli", "local_model", ("tiny", "base")),
        ("9Router adresi", "llm_url", ()),
        ("9Router modeli", "llm_model", ("scout-flash", "ulku")),
        ("9Router API anahtarı", "llm_key", ()),
    )

    def __init__(self, root, settings, settings_store, credentials, controller, events, tray=None):
        self.root, self.store, self.credentials = root, settings_store, credentials
        self.controller, self.events, self.tray = controller, events, tray
        self.vm = SettingsViewModel(settings)
        self.vars = {}
        self.widgets = {}
        self.root.title("Ses Yazıcı")
        self.root.configure(bg=COLORS["background"])
        self.root.geometry("620x540")
        self.root.minsize(560, 500)
        self._style()
        self._build(settings)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.after(80, self.poll_events)

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=COLORS["background"], foreground=COLORS["foreground"], font=FONT)
        style.configure("TEntry", fieldbackground=COLORS["input"], foreground=COLORS["input_foreground"],
                        bordercolor=COLORS["border"], lightcolor=COLORS["border"], darkcolor=COLORS["border"],
                        insertcolor=COLORS["input_foreground"], selectbackground=COLORS["selection"],
                        selectforeground=COLORS["input_foreground"], padding=6)
        style.map("TEntry",
                  fieldbackground=[("disabled", COLORS["card"]), ("focus", COLORS["input"])],
                  foreground=[("disabled", COLORS["disabled"]), ("focus", COLORS["input_foreground"])],
                  bordercolor=[("focus", COLORS["focus"]), ("!focus", COLORS["border"])])
        style.configure("TCombobox", fieldbackground=COLORS["input"], background=COLORS["input"],
                        foreground=COLORS["input_foreground"], bordercolor=COLORS["border"],
                        arrowcolor=COLORS["input_foreground"], selectbackground=COLORS["selection"],
                        selectforeground=COLORS["input_foreground"], padding=6, arrowsize=14)
        style.map("TCombobox",
                  fieldbackground=[("readonly", COLORS["input"]), ("focus", COLORS["input"]),
                                   ("disabled", COLORS["card"])],
                  foreground=[("readonly", COLORS["input_foreground"]), ("focus", COLORS["input_foreground"]),
                              ("disabled", COLORS["disabled"])],
                  bordercolor=[("focus", COLORS["focus"]), ("readonly", COLORS["border"])],
                  arrowcolor=[("readonly", COLORS["input_foreground"]), ("disabled", COLORS["disabled"])])
        self.root.option_add("*TCombobox*Listbox.background", COLORS["input"])
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["input_foreground"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["selection"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", COLORS["input_foreground"])
        style.configure("Primary.TButton", background=COLORS["primary"], foreground=COLORS["primary_foreground"],
                        bordercolor=COLORS["primary"], padding=(14, 8))
        style.map("Primary.TButton", background=[("active", COLORS["primary"]), ("focus", COLORS["primary"])],
                  bordercolor=[("focus", COLORS["focus"])])
        style.configure("Secondary.TButton", background=COLORS["secondary"], foreground=COLORS["secondary_foreground"],
                        bordercolor=COLORS["secondary"], padding=(12, 7))
        style.map("Secondary.TButton", background=[("active", COLORS["focus"]), ("focus", COLORS["secondary"])],
                  bordercolor=[("focus", COLORS["primary"])])
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("Card.TLabel", background=COLORS["card"], foreground=COLORS["foreground"])

    def _build(self, settings):
        card = ttk.Frame(self.root, style="Card.TFrame", padding=SPACING["xl"])
        card.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])
        ttk.Label(card, text="Ses Yazıcı", style="Card.TLabel", font=("Segoe UI Semibold", 16)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        saved_key = self.credentials.get("llm_api_key") or ""
        defaults = {
            "hotkey": settings.hotkey,
            "record_mode": settings.record_mode,
            "flow_mode": FLOW_MODE_NAMES[settings.flow_mode],
            "local_model": settings.stt.local_model,
            "llm_url": settings.llm.base_url,
            "llm_model": settings.llm.model,
            "llm_key": saved_key,
        }
        for row, (label, name, choices) in enumerate(self.FIELD_SPECS, 1):
            ttk.Label(card, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            var = tk.StringVar(value=defaults[name])
            self.vars[name] = var
            if choices:
                widget = ttk.Combobox(card, textvariable=var, values=choices, state="readonly")
                widget.grid(row=row, column=1, sticky="ew", pady=5)
            elif name == "llm_key":
                key_frame = ttk.Frame(card, style="Card.TFrame")
                key_frame.grid(row=row, column=1, sticky="ew", pady=5)
                key_frame.columnconfigure(0, weight=1)
                widget = ttk.Entry(key_frame, textvariable=var, show="*")
                widget.grid(row=0, column=0, sticky="ew")
                self.key_toggle = ttk.Button(key_frame, text="Göster", style="Secondary.TButton",
                                             command=self.toggle_key_visibility, takefocus=True)
                self.key_toggle.grid(row=0, column=1, padx=(SPACING["sm"], 0))
            else:
                widget = ttk.Entry(card, textvariable=var)
                widget.grid(row=row, column=1, sticky="ew", pady=5)
            self.widgets[name] = widget
        card.columnconfigure(1, weight=1)
        status_row = len(self.FIELD_SPECS) + 1
        self.status_var = tk.StringVar(value="Hazır")
        ttk.Label(card, text="Durum", style="Card.TLabel").grid(row=status_row, column=0, sticky="w", pady=(14, 5))
        ttk.Label(card, textvariable=self.status_var, style="Card.TLabel").grid(row=status_row, column=1, sticky="w", pady=(14, 5))
        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=status_row + 1, column=0, columnspan=2, sticky="e", pady=(14, 0))

        self.log_btn = ttk.Button(buttons, text="Logları Aç", style="Secondary.TButton", command=self.open_logs, takefocus=True)
        self.log_btn.pack(side="left", padx=5)
        self.test_btn = ttk.Button(buttons, text="Test Et", style="Secondary.TButton", command=self.test_action, takefocus=True)
        self.test_btn.pack(side="left", padx=5)
        self.save_btn = ttk.Button(buttons, text="Kaydet", style="Primary.TButton", command=self.save, takefocus=True)
        self.save_btn.pack(side="left")

    def toggle_key_visibility(self):
        entry = self.widgets["llm_key"]
        show, label = key_visibility(str(entry.cget("show")))
        entry.configure(show=show)
        self.key_toggle.configure(text=label)

    def values(self):
        return {name: var.get() for name, var in self.vars.items()}

    def open_logs(self):
        import app_logger
        app_logger.open_log_file()

    def save(self):
        try:
            key_value = self.vars["llm_key"].get().strip()
            if key_value:
                self.credentials.set("llm_api_key", key_value)
            else:
                self.credentials.delete("llm_api_key")
            settings = self.vm.build(self.values())
            self.controller.update_settings(settings)
            self.store.save(settings)
            self.vm.settings = settings
            self.status_var.set("Hazır: Ayarlar kaydedildi")
        except Exception as exc:
            messagebox.showerror("Ayar hatası", str(exc))

    def test_action(self):
        if self.controller.state == AppState.LISTENING:
            self.controller.stop_recording()
        else:
            self.controller.start_recording()

    def poll_events(self, reschedule: bool = True):
        try:
            while True:
                event = self.events.get_nowait()
                self.status_var.set(event.message)
                if event.state == AppState.LISTENING:
                    self.test_btn.configure(text="Durdur", state="normal")
                elif event.state in {AppState.TRANSCRIBING, AppState.CLEANING, AppState.INJECTING}:
                    self.test_btn.configure(text="İşleniyor...", state="disabled")
                elif event.state in {AppState.READY, AppState.WRITTEN, AppState.ERROR}:
                    self.test_btn.configure(text="Test Et", state="normal")
        except queue.Empty:
            pass
        if reschedule:
            self.root.after(80, self.poll_events)

    def hide(self):
        if self.tray:
            self.root.withdraw()
        else:
            self.exit()

    def show(self):
        self.root.after(0, self.root.deiconify)

    def exit(self):
        self.controller.shutdown()
        if self.tray:
            self.tray.stop()
        self.root.after(0, self.root.destroy)
