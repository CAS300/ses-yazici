from pathlib import Path


def test_documentation_checklist():
    text=Path(__file__).parents[1].joinpath("README.md").read_text(encoding="utf-8")
    required=[
        "API-only kurulum", "Yerel STT kurulumu", "Windows Credential Manager",
        "Tray ve çıkış", "text içindir", "Mikrofon açılmıyor",
        "Global kısayol çalışmıyor", "API/timeout", "requirements-local.txt",
        "Kombine (Yerel Whisper + 9Router LLM)",
        "Yalnızca Yerel (Ham / Çevrimdışı)", "Yalnızca 9Router / API",
        "`base`", "API anahtarı veya ağ gerektirmez", "ilk kullanımda modeli indirmek",
    ]
    assert all(item in text for item in required)
