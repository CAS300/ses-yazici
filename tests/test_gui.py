from pathlib import Path

from gui import AppGui, SettingsViewModel
from settings import AppSettings
from ui_tokens import COLORS


def test_view_model_builds_valid_settings():
    values={"hotkey":" F9 ","record_mode":"push_to_talk","stt_provider":"local","stt_url":"https://api.openai.com/v1","stt_model":"whisper-1","local_model":"base","llm_url":"https://router.erensahin.tr/v1","llm_model":"ulku","stt_key":"","llm_key":""}
    result=SettingsViewModel(AppSettings()).build(values)
    assert (result.hotkey,result.record_mode,result.stt.provider,result.stt.local_model,result.llm.model)==("f9","push_to_talk","local","base","ulku")


def test_all_required_fields_have_labels_and_keys_are_masked():
    labels=[x[0] for x in AppGui.FIELD_SPECS]; names=[x[1] for x in AppGui.FIELD_SPECS]
    assert labels == ["Global kısayol","Kayıt modu","STT sağlayıcısı","STT API adresi","STT API modeli","Yerel STT modeli","9Router adresi","9Router modeli","STT API anahtarı","9Router API anahtarı"]
    source=Path(__file__).parents[1].joinpath("gui.py").read_text(encoding="utf-8")
    assert 'show="*" if name.endswith("_key")' in source
    assert "#" not in source  # colors live only in ui_tokens


def test_house_tokens_and_status_text():
    assert COLORS["background"]=="#0a0a0b" and COLORS["primary"]=="#22c55e"
