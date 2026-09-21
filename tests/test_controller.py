import queue
from dataclasses import replace
from types import SimpleNamespace

import pytest

from audio_recorder import AudioClip
from controller import AppController, AppState
from settings import AppSettings


class ImmediateThread:
    def __init__(self,target,**kw): self.target=target; self.alive=False
    def start(self): self.alive=True; self.target(); self.alive=False
    def is_alive(self): return self.alive
    def join(self,timeout=None): pass
class Recorder:
    def __init__(self): self.starts=0; self.cancels=0
    def start(self,**kw): self.starts+=1
    def stop(self): return AudioClip(b"\0\0"*20,16000,1)
    def cancel(self): self.cancels+=1
class Stt:
    def __init__(self,error=False,text="raw"): self.error=error; self.text=text
    def transcribe(self,*a,**kw):
        if self.error: raise RuntimeError("secret detail")
        return self.text
class Cleaner:
    def __init__(self,error=False): self.error=error; self.calls=[]
    def clean(self,text):
        self.calls.append(text)
        if self.error: raise RuntimeError("private transcript")
        return "clean"
class Injector:
    def __init__(self,error=False): self.calls=[]; self.error=error
    def paste(self,text):
        self.calls.append(text)
        if self.error: raise RuntimeError("paste detail")
class Hotkeys:
    def __init__(self): self.unregisters=0
    def unregister(self): self.unregisters+=1
    def register(self,*a): pass
class Resource:
    def __init__(self): self.closes=0
    def close(self): self.closes+=1


def make(mode="combined", **kw):
    parts=dict(recorder=Recorder(), transcriber=Stt(), cleaner=Cleaner(), injector=Injector())
    parts.update(kw); events=queue.Queue()
    settings = replace(AppSettings(), flow_mode=mode)
    c=AppController(**parts, settings=settings, events=events, thread_factory=ImmediateThread)
    events.get()
    return c,parts,events


def run_pipeline(controller, events):
    controller.start_recording(); controller.stop_recording()
    states=[]
    while not events.empty(): states.append(events.get().state)
    return states


@pytest.mark.parametrize("mode", ["combined", "api_only"])
def test_remote_modes_clean_once_and_state_trace(mode):
    c,p,e=make(mode); c.start_recording(); c.start_recording(); c.stop_recording()
    assert p["recorder"].starts == 1
    assert p["cleaner"].calls == ["raw"] and p["injector"].calls == ["clean"]
    states=[]
    while not e.empty(): states.append(e.get().state)
    assert states == [AppState.LISTENING,AppState.TRANSCRIBING,AppState.CLEANING,AppState.INJECTING,AppState.WRITTEN,AppState.READY]


def test_local_only_preserves_raw_and_skips_cleaning():
    raw = "  şey, merhaba!  \n"
    cleaner = Cleaner()
    c,p,e=make("local_only", transcriber=Stt(text=raw), cleaner=cleaner)
    states = run_pipeline(c, e)
    assert cleaner.calls == []
    assert p["injector"].calls == [raw]
    assert states == [AppState.LISTENING,AppState.TRANSCRIBING,AppState.INJECTING,AppState.WRITTEN,AppState.READY]


def test_missing_cleaner_in_remote_mode_is_sanitized_error():
    c,p,e=make("combined", cleaner=None)
    states = run_pipeline(c, e)
    assert p["injector"].calls == [] and c.state == AppState.ERROR
    assert states[-1] == AppState.ERROR


@pytest.mark.parametrize("parts", [
    {"transcriber": Stt(error=True)},
    {"cleaner": Cleaner(error=True)},
    {"transcriber": Stt(text=" ")},
    {"injector": Injector(error=True)},
])
def test_service_errors_do_not_report_success_or_leak_details(parts):
    c,p,e=make(**parts)
    states = run_pipeline(c, e)
    messages = []
    while not e.empty(): messages.append(e.get().message)
    assert c.state == AppState.ERROR
    assert AppState.WRITTEN not in states
    if not isinstance(parts.get("injector"), Injector) or not parts.get("injector").error:
        assert p["injector"].calls == []
    assert all(detail not in " ".join(messages) for detail in ("secret detail", "private transcript", "paste detail"))


def test_local_only_blank_transcript_does_not_paste():
    c,p,e=make("local_only", transcriber=Stt(text=" \n"))
    run_pipeline(c, e)
    assert p["injector"].calls == [] and c.state == AppState.ERROR


def test_shutdown_closes_resources():
    h=Hotkeys(); r=Resource(); c,p,e=make(); c.hotkeys=h; c.resources=[r]; c.shutdown()
    assert p["recorder"].cancels==1 and h.unregisters==1 and r.closes==1
