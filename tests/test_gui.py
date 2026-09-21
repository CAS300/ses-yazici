from pathlib import Path

from gui import AppGui, FLOW_MODE_LABELS, SettingsViewModel, key_visibility
from settings import AppSettings, SttSettings
from ui_tokens import COLORS


def test_a3_view_model_builds_only_local_stt_shape():
    values={"hotkey":" F9 ","record_mode":"push_to_talk","flow_mode":"Yalnızca Yerel (Ham / Çevrimdışı)",
            "local_model":"tiny","llm_url":"https://router.erensahin.tr/v1","llm_model":"ulku","llm_key":""}
    result=SettingsViewModel(AppSettings()).build(values)
    assert (result.hotkey,result.record_mode,result.flow_mode)==("f9","push_to_talk","local_only")
    assert result.stt == SttSettings(local_model="tiny", language="tr")
    assert result.llm.model == "ulku"


def test_a3_exact_mode_and_field_inventory():
    assert FLOW_MODE_LABELS == {
        "Kombine (Yerel Whisper + 9Router LLM)": "combined",
        "Yalnızca Yerel (Ham / Çevrimdışı)": "local_only",
    }
    labels=[x[0] for x in AppGui.FIELD_SPECS]; names=[x[1] for x in AppGui.FIELD_SPECS]
    assert labels == ["Global kısayol","Kayıt modu","Çalışma modu","Yerel STT modeli",
                      "9Router adresi","9Router modeli","9Router API anahtarı"]
    assert not {"stt_url", "stt_model", "stt_key"} & set(names)
    assert next(x for x in AppGui.FIELD_SPECS if x[1] == "flow_mode")[2] == tuple(FLOW_MODE_LABELS)
    assert next(x for x in AppGui.FIELD_SPECS if x[1] == "local_model")[2] == ("tiny", "base")


def test_a8_house_tokens_are_locked():
    assert COLORS["background"] == "#1e1e2e"
    assert COLORS["card"] == "#1e1e2e"
    assert COLORS["input"] == "#2d2d3f"
    assert COLORS["foreground"] == COLORS["input_foreground"] == "#ffffff"
    assert COLORS["primary"] == "#22c55e"
    assert COLORS["secondary"] == "#3b82f6"
    assert COLORS["focus"] == COLORS["secondary"]


def test_a8_styles_are_tokenized_and_cover_widget_states():
    source=Path(__file__).parents[1].joinpath("gui.py").read_text(encoding="utf-8")
    assert "#" not in source
    for fragment in ('style.configure("TEntry"', 'style.map("TEntry"',
                     'style.configure("TCombobox"', 'style.map("TCombobox"',
                     'option_add("*TCombobox*Listbox.background"', 'Secondary.TButton'):
        assert fragment in source
    for state in ("focus", "disabled", "readonly"):
        assert state in source


def test_a9_visibility_helper_preserves_value_and_toggles_label():
    assert key_visibility("*") == ("", "Gizle")
    assert key_visibility("") == ("*", "Göster")


def test_a7_a9_gui_has_only_masked_llm_key_and_accessible_toggle():
    source=Path(__file__).parents[1].joinpath("gui.py").read_text(encoding="utf-8")
    assert 'show="*"' in source
    assert 'text="Göster"' in source
    assert 'takefocus=True' in source
    assert 'self.credentials.set("llm_api_key"' in source
    assert "stt_api_key" not in source
