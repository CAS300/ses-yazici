import queue
from dataclasses import replace

import pytest

from controller import AppController
from settings import AppSettings
from tests.test_controller import ImmediateThread, Recorder

@pytest.mark.parametrize("mode,raw,cleaned,expected", [
    ("combined","ham","temiz",["audio:start","audio:wav","local-stt","llm:clean","clipboard:temiz"]),
    ("local_only","  ham!  ",None,["audio:start","audio:wav","local-stt","clipboard:  ham!  "]),
])
def test_a4_a5_two_mode_pipeline_trace(mode,raw,cleaned,expected):
    trace=[]
    class R(Recorder):
        def start(self,**kw): trace.append("audio:start"); super().start(**kw)
        def stop(self): trace.append("audio:wav"); return super().stop()
    class S:
        def transcribe(self,wav_bytes,language): trace.append("local-stt"); return raw
    class C:
        def clean(self,text): trace.append("llm:clean"); return cleaned
    class I:
        def paste(self,text): trace.append(f"clipboard:{text}")
    c=AppController(R(),S(),None if mode=="local_only" else C(),I(),replace(AppSettings(),flow_mode=mode),events=queue.Queue(),thread_factory=ImmediateThread)
    c.start_recording(); c.stop_recording(); assert trace == expected
