import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_a12_documentation_checklist():
    text = ROOT.joinpath("README.md").read_text(encoding="utf-8")
    required = [
        "combined",
        "local_only",
        "Kombine (Yerel Whisper + 9Router LLM)",
        "Yalnızca Yerel (Ham / Çevrimdışı)",
        "`tiny`",
        "`base`",
        "F8",
        "F9",
        "F10",
        "F12",
        "Ctrl+Alt+Space",
        "Ctrl+Shift+D",
        "pynput",
        "app.log",
        "Logları Aç",
        "Dinleniyor...",
        "pythonw.exe",
        "requirements-local.txt",
        "ilk kullanımda modeli indirmek",
        "yalnız 9Router",
        "Windows Credential Manager",
        "error.log",
    ]
    for item in required:
        assert item in text, f"README.md missing required term: {item}"

    for forbidden in ("api_only", "stt_api_key", "api_base_url", "api_model", "whisper-1", "STT API", "keyboard"):
        assert forbidden not in text, f"README.md contains forbidden term: {forbidden}"


def test_a12_config_example_is_local_stt_only():
    raw = ROOT.joinpath("config.example.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    assert data["flow_mode"] in {"combined", "local_only"}
    assert data["stt"] == {"local_model": "base", "language": "tr"}
    for forbidden in ("api_only", "stt_api_key", "api_base_url", "api_model", "whisper-1", "provider"):
        assert forbidden not in raw, f"config.example.json contains forbidden term: {forbidden}"
