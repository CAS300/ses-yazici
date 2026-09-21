import queue
from dataclasses import replace

import pytest

from controller import AppController
from settings import AppSettings
from tests.test_controller import ImmediateThread, Recorder


@pytest.mark.parametrize(
    "mode,stt_step,raw,cleaned,expected",
    [
        (
            "combined", "local-stt", "ham", "temiz",
            ["audio:start", "audio:wav", "local-stt", "llm:clean", "clipboard:temiz", "keyboard:ctrl+v"],
        ),
        (
            "local_only", "local-stt", "  ham!  ", None,
            ["audio:start", "audio:wav", "local-stt", "clipboard:  ham!  ", "keyboard:ctrl+v"],
        ),
        (
            "api_only", "api-stt", "ham", "temiz",
            ["audio:start", "audio:wav", "api-stt", "llm:clean", "clipboard:temiz", "keyboard:ctrl+v"],
        ),
    ],
)
def test_mode_pipeline_trace(mode, stt_step, raw, cleaned, expected):
    trace=[]

    class R(Recorder):
        def start(self,**kw): trace.append("audio:start"); super().start(**kw)
        def stop(self): trace.append("audio:wav"); return super().stop()

    class S:
        def transcribe(self,wav_bytes,language): trace.append(stt_step); return raw

    class C:
        def clean(self,text): trace.append("llm:clean"); return cleaned

    class I:
        def paste(self,text): trace.append(f"clipboard:{text}"); trace.append("keyboard:ctrl+v")

    settings = replace(AppSettings(), flow_mode=mode)
    events=queue.Queue()
    cleaner = None if mode == "local_only" else C()
    controller=AppController(R(),S(),cleaner,I(),settings,events=events,thread_factory=ImmediateThread)
    controller.start_recording(); controller.stop_recording()
    assert trace == expected
