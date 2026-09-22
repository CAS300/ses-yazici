import queue
from dataclasses import replace

import pytest

from audio_recorder import AudioClip
from controller import AppController, AppState, MIN_RECORDING_SECONDS
from settings import AppSettings
from transcriber import TranscriptionError


class ImmediateThread:
    def __init__(self, target, **kw):
        self.target = target
        self.alive = False

    def start(self):
        self.alive = True
        self.target()
        self.alive = False

    def is_alive(self):
        return self.alive

    def join(self, timeout=None):
        pass


class Recorder:
    def __init__(self, clip=None):
        self.starts = 0
        self.cancels = 0
        self.clip = clip or AudioClip(b"\0\0" * 4800, 16000, 1)

    def start(self, **kw):
        self.starts += 1

    def stop(self):
        return self.clip

    def cancel(self):
        self.cancels += 1


class Stt:
    def __init__(self, error=False, text="raw", exception=None):
        self.error = error
        self.text = text
        self.exception = exception
        self.calls = 0

    def transcribe(self, *a, **kw):
        self.calls += 1
        if self.exception:
            raise self.exception
        if self.error:
            raise RuntimeError("secret detail")
        return self.text


class Cleaner:
    def __init__(self, error=False):
        self.error = error
        self.calls = []

    def clean(self, text):
        self.calls.append(text)
        if self.error:
            raise RuntimeError("private transcript")
        return "clean"


class Injector:
    def __init__(self, error=False):
        self.calls = []
        self.error = error

    def paste(self, text):
        self.calls.append(text)
        if self.error:
            raise RuntimeError("paste detail")


def make(mode="combined", **kw):
    parts = dict(recorder=Recorder(), transcriber=Stt(), cleaner=Cleaner(), injector=Injector())
    parts.update(kw)
    events = queue.Queue()
    controller = AppController(
        **parts,
        settings=replace(AppSettings(), flow_mode=mode),
        events=events,
        thread_factory=ImmediateThread,
    )
    events.get()
    return controller, parts, events


def run_pipeline(controller, events):
    controller.start_recording()
    controller.stop_recording()
    states = []
    while not events.empty():
        states.append(events.get().state)
    return states


def test_a4_combined_cleans_once_and_pastes_once():
    controller, parts, events = make("combined")
    states = run_pipeline(controller, events)
    assert parts["cleaner"].calls == ["raw"]
    assert parts["injector"].calls == ["clean"]
    assert states == [
        AppState.LISTENING,
        AppState.TRANSCRIBING,
        AppState.CLEANING,
        AppState.INJECTING,
        AppState.WRITTEN,
        AppState.READY,
    ]


def test_a5_local_only_preserves_exact_raw_and_skips_cleaner():
    raw = "  şey, merhaba!  \n"
    cleaner = Cleaner()
    controller, parts, events = make("local_only", transcriber=Stt(text=raw), cleaner=cleaner)
    states = run_pipeline(controller, events)
    assert cleaner.calls == []
    assert parts["injector"].calls == [raw]
    assert AppState.CLEANING not in states


@pytest.mark.parametrize(
    "parts",
    [
        {"transcriber": Stt(error=True)},
        {"cleaner": Cleaner(error=True)},
        {"injector": Injector(error=True)},
    ],
)
def test_errors_never_paste_success_or_leak(parts):
    controller, _, events = make(**parts)
    states = run_pipeline(controller, events)
    messages = []
    while not events.empty():
        messages.append(events.get().message)
    assert controller.state == AppState.ERROR
    assert AppState.WRITTEN not in states
    assert all(
        value not in " ".join(messages)
        for value in ("secret detail", "private transcript", "paste detail")
    )


@pytest.mark.parametrize("mode", ["combined", "local_only"])
def test_blank_transcription_returns_ready_without_clean_or_paste(mode, caplog):
    controller, parts, events = make(mode, transcriber=Stt(text=" \n"))

    with caplog.at_level("INFO"):
        states = run_pipeline(controller, events)

    assert parts["cleaner"].calls == []
    assert parts["injector"].calls == []
    assert controller.state == AppState.READY
    assert AppState.WRITTEN not in states
    assert AppState.ERROR not in states
    assert states[-1] == AppState.READY
    assert "Konuşma algılanmadı" in caplog.text


def test_legacy_empty_transcription_error_returns_ready_without_downstream_calls():
    stt = Stt(exception=TranscriptionError("Transkripsiyon boş döndü."))
    controller, parts, events = make(transcriber=stt)

    states = run_pipeline(controller, events)

    assert controller.state == AppState.READY
    assert parts["cleaner"].calls == []
    assert parts["injector"].calls == []
    assert AppState.ERROR not in states


def test_other_transcription_error_remains_error_and_does_not_paste():
    stt = Stt(exception=TranscriptionError("Model yüklenemedi."))
    controller, parts, events = make(transcriber=stt)

    states = run_pipeline(controller, events)

    assert controller.state == AppState.ERROR
    assert parts["cleaner"].calls == []
    assert parts["injector"].calls == []
    assert AppState.WRITTEN not in states


def test_short_recording_returns_ready_without_downstream_calls(caplog):
    clip = AudioClip(b"\0\0" * 4799, 16000, 1)
    controller, parts, events = make(recorder=Recorder(clip))

    with caplog.at_level("INFO"):
        states = run_pipeline(controller, events)

    assert states == [AppState.LISTENING, AppState.TRANSCRIBING, AppState.READY]
    assert controller.state == AppState.READY
    assert parts["transcriber"].calls == 0
    assert parts["cleaner"].calls == []
    assert parts["injector"].calls == []
    assert AppState.ERROR not in states
    assert AppState.WRITTEN not in states
    assert "Kısa kayıt" in caplog.text


def test_recording_at_exact_boundary_continues_pipeline():
    frames = int(16000 * MIN_RECORDING_SECONDS)
    clip = AudioClip(b"\0\0" * frames, 16000, 1)
    controller, parts, events = make(recorder=Recorder(clip))

    run_pipeline(controller, events)

    assert parts["transcriber"].calls == 1


def test_error_state_accepts_a_new_recording():
    controller, parts, events = make()
    controller._emit(AppState.ERROR)

    controller.start_recording()

    assert parts["recorder"].starts == 1
    assert controller.state == AppState.LISTENING
    states = []
    while not events.empty():
        states.append(events.get().state)
    assert states[-1] == AppState.LISTENING


@pytest.mark.parametrize(
    "state",
    [
        AppState.LISTENING,
        AppState.TRANSCRIBING,
        AppState.CLEANING,
        AppState.INJECTING,
        AppState.WRITTEN,
    ],
)
def test_busy_states_reject_recording_reentry(state):
    controller, parts, _ = make()
    controller._emit(state)

    controller.start_recording()

    assert parts["recorder"].starts == 0
    assert controller.state == state


def test_shutdown_rejects_recording_start():
    controller, parts, _ = make()
    controller.shutdown()

    controller.start_recording()

    assert parts["recorder"].starts == 0
