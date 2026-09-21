import queue
from dataclasses import replace

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

def make(mode="combined", **kw):
    parts=dict(recorder=Recorder(), transcriber=Stt(), cleaner=Cleaner(), injector=Injector())
    parts.update(kw); events=queue.Queue()
    c=AppController(**parts, settings=replace(AppSettings(), flow_mode=mode), events=events, thread_factory=ImmediateThread)
    events.get(); return c,parts,events

def run_pipeline(c,e):
    c.start_recording(); c.stop_recording(); states=[]
    while not e.empty(): states.append(e.get().state)
    return states

def test_a4_combined_cleans_once_and_pastes_once():
    c,p,e=make("combined"); states=run_pipeline(c,e)
    assert p["cleaner"].calls == ["raw"] and p["injector"].calls == ["clean"]
    assert states == [AppState.LISTENING,AppState.TRANSCRIBING,AppState.CLEANING,AppState.INJECTING,AppState.WRITTEN,AppState.READY]

def test_a5_local_only_preserves_exact_raw_and_skips_cleaner():
    raw="  şey, merhaba!  \n"; cleaner=Cleaner()
    c,p,e=make("local_only",transcriber=Stt(text=raw),cleaner=cleaner); states=run_pipeline(c,e)
    assert cleaner.calls == [] and p["injector"].calls == [raw]
    assert AppState.CLEANING not in states

@pytest.mark.parametrize("parts", [{"transcriber":Stt(error=True)},{"cleaner":Cleaner(error=True)},
                                    {"transcriber":Stt(text=" ")},{"injector":Injector(error=True)}])
def test_errors_never_paste_success_or_leak(parts):
    c,p,e=make(**parts); states=run_pipeline(c,e); messages=[]
    while not e.empty(): messages.append(e.get().message)
    assert c.state == AppState.ERROR and AppState.WRITTEN not in states
    assert all(x not in " ".join(messages) for x in ("secret detail","private transcript","paste detail"))

def test_local_blank_does_not_paste():
    c,p,e=make("local_only",transcriber=Stt(text=" \n")); run_pipeline(c,e)
    assert p["injector"].calls == [] and c.state == AppState.ERROR
