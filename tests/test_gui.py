from pathlib import Path

from gui import AppGui, FLOW_MODE_LABELS, SettingsViewModel
from settings import AppSettings
from ui_tokens import COLORS


def test_view_model_builds_valid_settings():
    values={"hotkey":" F9 ","record_mode":"push_to_talk","flow_mode":"Yalnızca Yerel (Ham / Çevrimdışı)","stt_url":"https://api.openai.com/v1","stt_model":"whisper-1","local_model":"base","llm_url":"https://router.erensahin.tr/v1","llm_model":"ulku","stt_key":"","llm_key":""}
    result=SettingsViewModel(AppSettings()).build(values)
    assert (result.hotkey,result.record_mode,result.flow_mode,result.stt.local_model,result.llm.model)==("f9","push_to_talk","local_only","base","ulku")


def test_flow_mode_labels_are_canonical_and_provider_field_is_removed():
    assert FLOW_MODE_LABELS == {
        "Kombine (Yerel Whisper + 9Router LLM)": "combined",
        "Yalnızca Yerel (Ham / Çevrimdışı)": "local_only",
        "Yalnızca 9Router / API": "api_only",
    }
    labels=[x[0] for x in AppGui.FIELD_SPECS]; names=[x[1] for x in AppGui.FIELD_SPECS]
    assert labels == ["Global kısayol","Kayıt modu","Çalışma modu","STT API adresi","STT API modeli","Yerel STT modeli","9Router adresi","9Router modeli","STT API anahtarı","9Router API anahtarı"]
    assert "stt_provider" not in names
    flow_spec = next(spec for spec in AppGui.FIELD_SPECS if spec[1] == "flow_mode")
    assert flow_spec[2] == tuple(FLOW_MODE_LABELS)


def test_keys_are_masked_and_colors_live_in_tokens():
    source=Path(__file__).parents[1].joinpath("gui.py").read_text(encoding="utf-8")
    assert 'show="*" if name.endswith("_key")' in source
    assert 'state="readonly"' in source
    assert "#" not in source  # colors live only in ui_tokens


def test_house_tokens_and_status_text():
    assert COLORS["background"]=="#0a0a0b" and COLORS["primary"]=="#22c55e"
