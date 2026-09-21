import pytest
from pynput.keyboard import Key, KeyCode, Listener

from hotkeys import HotkeyError, HotkeyService, hotkey_to_pynput


class MockListener:
    def __init__(self, on_press, on_release):
        self.on_press = on_press
        self.on_release = on_release
        self.running = False
        self.stopped = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        self.stopped = True

    def canonical(self, key):
        # Delegate to real Listener.canonical for accurate key normalization
        try:
            return Listener(lambda k: None).canonical(key)
        except Exception:
            return key


class MockListenerFactory:
    def __init__(self):
        self.listeners = []
        self.fail = False

    def __call__(self, on_press, on_release):
        if self.fail:
            raise RuntimeError("listener start failed")
        listener = MockListener(on_press, on_release)
        self.listeners.append(listener)
        return listener


def test_hotkey_to_pynput_mapping():
    assert hotkey_to_pynput("F8") == "<f8>"
    assert hotkey_to_pynput("F9") == "<f9>"
    assert hotkey_to_pynput("F10") == "<f10>"
    assert hotkey_to_pynput("F12") == "<f12>"
    assert hotkey_to_pynput("Ctrl+Alt+Space") == "<ctrl>+<alt>+<space>"
    assert hotkey_to_pynput("Ctrl+Shift+D") == "<ctrl>+<shift>+d"


def test_toggle_down_repeat_release_then_next_down():
    factory = MockListenerFactory()
    service = HotkeyService(listener_factory=factory)
    trace = []
    service.register("F8", "toggle", lambda: trace.append("start"), lambda: trace.append("stop"))

    listener = factory.listeners[-1]
    # First press
    listener.on_press(Key.f8)
    # Autorepeat while held
    listener.on_press(Key.f8)
    # Release
    listener.on_release(Key.f8)
    # Second press (toggle off)
    listener.on_press(Key.f8)
    # Release
    listener.on_release(Key.f8)

    assert trace == ["start", "stop"]


def test_ptt_repeat_and_extra_release_are_noops():
    factory = MockListenerFactory()
    service = HotkeyService(listener_factory=factory)
    trace = []
    service.register("F8", "push_to_talk", lambda: trace.append("start"), lambda: trace.append("stop"))

    listener = factory.listeners[-1]
    # First press
    listener.on_press(Key.f8)
    # Repeat while held
    listener.on_press(Key.f8)
    # Release (triggers stop)
    listener.on_release(Key.f8)
    # Extra release
    listener.on_release(Key.f8)

    assert trace == ["start", "stop"]


def test_combination_hotkey_ctrl_alt_space_ptt():
    factory = MockListenerFactory()
    service = HotkeyService(listener_factory=factory)
    trace = []
    service.register("Ctrl+Alt+Space", "push_to_talk", lambda: trace.append("start"), lambda: trace.append("stop"))

    listener = factory.listeners[-1]
    # Press modifiers then space
    listener.on_press(Key.ctrl_l)
    listener.on_press(Key.alt_l)
    listener.on_press(Key.space)
    assert trace == ["start"]

    # Release space -> stop
    listener.on_release(Key.space)
    assert trace == ["start", "stop"]

    listener.on_release(Key.alt_l)
    listener.on_release(Key.ctrl_l)
    assert trace == ["start", "stop"]


def test_callback_failure_does_not_commit_state_and_recovers():
    factory = MockListenerFactory()
    service = HotkeyService(listener_factory=factory)
    trace = []
    starts = [0]

    def start():
        starts[0] += 1
        if starts[0] == 1:
            raise RuntimeError("boom")
        trace.append("start")

    service.register("F8", "toggle", start, lambda: trace.append("stop"))
    listener = factory.listeners[-1]

    # First attempt fails in start callback
    listener.on_press(Key.f8)
    listener.on_release(Key.f8)
    assert trace == []

    # Second attempt succeeds
    listener.on_press(Key.f8)
    listener.on_release(Key.f8)
    assert trace == ["start"]

    # Third attempt stops
    listener.on_press(Key.f8)
    listener.on_release(Key.f8)
    assert trace == ["start", "stop"]


def test_partial_reregister_failure_keeps_old_listener():
    factory = MockListenerFactory()
    service = HotkeyService(listener_factory=factory)
    trace = []
    service.register("F8", "push_to_talk", lambda: trace.append("old-start"), lambda: trace.append("old-stop"))

    old_listener = factory.listeners[-1]
    assert old_listener.running is True

    # Simulate failure on next register
    factory.fail = True
    with pytest.raises(HotkeyError):
        service.register("F9", "push_to_talk", lambda: trace.append("new-start"), lambda: None)

    # Old listener should not be stopped
    assert old_listener.stopped is False

    # Old listener still receives events and works
    old_listener.on_press(Key.f8)
    old_listener.on_release(Key.f8)
    assert trace == ["old-start", "old-stop"]


def test_invalid_hotkey_or_mode_raises_hotkey_error():
    service = HotkeyService(listener_factory=MockListenerFactory())
    with pytest.raises(HotkeyError, match="Geçersiz kısayol"):
        service.register("InvalidKey", "toggle", lambda: None, lambda: None)

    with pytest.raises(HotkeyError, match="Geçersiz kayıt modu"):
        service.register("F8", "invalid_mode", lambda: None, lambda: None)


def test_unregister_cleans_up():
    factory = MockListenerFactory()
    service = HotkeyService(listener_factory=factory)
    service.register("F8", "toggle", lambda: None, lambda: None)
    listener = factory.listeners[-1]
    assert listener.running is True

    service.unregister()
    assert listener.stopped is True
    assert service._listener is None
    assert service._registration is None
