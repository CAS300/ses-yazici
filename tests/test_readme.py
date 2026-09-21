import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_a12_documentation_checklist():
    text=ROOT.joinpath("README.md").read_text(encoding="utf-8")
    required=["combined", "local_only", "Kombine (Yerel Whisper + 9Router LLM)",
              "Yalnızca Yerel (Ham / Çevrimdışı)", "`tiny`", "`base`", "F8",
              "pythonw.exe", "requirements-local.txt", "ilk kullanımda modeli indirmek",
              "yalnız 9Router", "Windows Credential Manager", "error.log"]
    assert all(item in text for item in required)
    for forbidden in ("api_only", "stt_api_key", "api_base_url", "api_model", "whisper-1", "STT API"):
        assert forbidden not in text


def test_a12_config_example_is_local_stt_only():
    raw=ROOT.joinpath("config.example.json").read_text(encoding="utf-8")
    data=json.loads(raw)
    assert data["flow_mode"] in {"combined", "local_only"}
    assert data["stt"] == {"local_model": "base", "language": "tr"}
    for forbidden in ("api_only", "stt_api_key", "api_base_url", "api_model", "whisper-1", "provider"):
        assert forbidden not in raw
