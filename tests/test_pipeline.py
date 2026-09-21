from tests.test_controller import ImmediateThread, Recorder
from controller import AppController
from settings import AppSettings
import queue


def test_hotkey_to_clipboard_pipeline_trace():
    trace=[]
    class R(Recorder):
        def start(self,**kw): trace.append("audio:start"); super().start(**kw)
        def stop(self): trace.append("audio:wav"); return super().stop()
    class S:
        def transcribe(self,wav_bytes,language): trace.append("stt:tr"); return "ham"
    class C:
        def clean(self,text): trace.append("llm:clean"); return "temiz"
    class I:
        def paste(self,text): trace.append("clipboard:temiz"); trace.append("keyboard:ctrl+v")
    events=queue.Queue(); controller=AppController(R(),S(),C(),I(),AppSettings(),events=events,thread_factory=ImmediateThread)
    controller.start_recording(); controller.stop_recording()
    assert trace == ["audio:start","audio:wav","stt:tr","llm:clean","clipboard:temiz","keyboard:ctrl+v"]
