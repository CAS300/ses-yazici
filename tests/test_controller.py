import queue
from types import SimpleNamespace

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
    def __init__(self,error=False): self.error=error
    def clean(self,text):
        if self.error: raise RuntimeError("private transcript")
        return "clean"
class Injector:
    def __init__(self): self.calls=[]
    def paste(self,text): self.calls.append(text)
class Hotkeys:
    def __init__(self): self.unregisters=0
    def unregister(self): self.unregisters+=1
    def register(self,*a): pass
class Resource:
    def __init__(self): self.closes=0
    def close(self): self.closes+=1


def make(**kw):
    parts=dict(recorder=Recorder(), transcriber=Stt(), cleaner=Cleaner(), injector=Injector())
    parts.update(kw); events=queue.Queue()
    c=AppController(**parts, settings=AppSettings(), events=events, thread_factory=ImmediateThread)
    events.get()
    return c,parts,events


def test_happy_path_state_trace_and_call_order():
    c,p,e=make(); c.start_recording(); c.start_recording(); c.stop_recording()
    assert p["recorder"].starts == 1 and p["injector"].calls == ["clean"]
    states=[]
    while not e.empty(): states.append(e.get().state)
    assert states == [AppState.LISTENING,AppState.TRANSCRIBING,AppState.CLEANING,AppState.INJECTING,AppState.WRITTEN,AppState.READY]


def test_stt_or_cleaner_error_never_pastes():
    for args in ({"transcriber":Stt(error=True)},{"cleaner":Cleaner(error=True)},{"transcriber":Stt(text=" ")}):
        c,p,e=make(**args); c.start_recording(); c.stop_recording()
        assert p["injector"].calls == [] and c.state == AppState.ERROR
        assert "secret" not in e.get().message if not e.empty() else True


def test_shutdown_closes_resources():
    h=Hotkeys(); r=Resource(); c,p,e=make(); c.hotkeys=h; c.resources=[r]; c.shutdown()
    assert p["recorder"].cancels==1 and h.unregisters==1 and r.closes==1
