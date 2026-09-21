import importlib


def test_modules_import():
    for name in ("settings", "ui_tokens", "audio_recorder", "transcriber", "llm_cleaner", "text_injector", "hotkeys", "controller", "gui", "main"):
        importlib.import_module(name)
