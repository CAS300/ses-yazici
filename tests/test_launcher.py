from pathlib import Path


def test_a11_launcher_uses_quoted_pythonw_without_console_fallback():
    text=Path(__file__).parents[1].joinpath("baslat.bat").read_text(encoding="utf-8")
    lower=text.lower()
    assert "pythonw.exe" in lower
    assert "python.exe" not in lower
    assert "pause" not in lower
    assert "\necho " not in lower
    assert "%~dp0" in text
    assert '"%~dp0main.py"' in text
