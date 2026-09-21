import pytest
from pynput.keyboard import Key

from text_injector import InjectionError, PynputKeyboardAdapter, TextInjector


class Clipboard:
    def __init__(self, value="old"):
        self.value = value
        self.trace = []

    def paste(self):
        self.trace.append(("get", self.value))
        return self.value

    def copy(self, value):
        self.trace.append(("set", value))
        self.value = value


class Keyboard:
    def __init__(self, clipboard=None, external=None):
        self.trace = []
        self.clipboard = clipboard
        self.external = external

    def send(self, value):
        self.trace.append(value)
        if self.external is not None:
            self.clipboard.value = self.external


class MockController:
    def __init__(self):
        self.events = []

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))


def test_paste_and_restore_order():
    cb = Clipboard()
    kb = Keyboard()
    injector = TextInjector(cb, kb, sleep=lambda _: None)
    injector.paste("new")
    assert kb.trace == ["ctrl+v"] and cb.value == "old"
    assert cb.trace == [("get", "old"), ("set", "new"), ("get", "new"), ("set", "old")]


def test_external_clipboard_change_is_not_overwritten():
    cb = Clipboard()
    kb = Keyboard(cb, "external")
    TextInjector(cb, kb, sleep=lambda _: None).paste("new")
    assert cb.value == "external"


def test_empty_text_sends_no_key():
    cb = Clipboard()
    kb = Keyboard()
    with pytest.raises(InjectionError):
        TextInjector(cb, kb).paste("  ")
    assert kb.trace == []


def test_pynput_keyboard_adapter_ctrl_v():
    controller = MockController()
    adapter = PynputKeyboardAdapter(controller=controller)
    adapter.send("ctrl+v")
    assert controller.events == [
        ("press", Key.ctrl),
        ("press", "v"),
        ("release", "v"),
        ("release", Key.ctrl),
    ]


def test_pynput_keyboard_adapter_ignores_unsupported_key():
    controller = MockController()
    adapter = PynputKeyboardAdapter(controller=controller)
    adapter.send("unsupported")
    assert controller.events == []
