import queue
from dataclasses import replace

import pytest

from audio_recorder import AudioClip
from controller import AppController, AppState
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


def test_short_clip_skips_downstream_returns_ready_and_accepts_next_recording():
    trace = []

    class R(Recorder):
        def __init__(self):
            super().__init__(AudioClip(b"\0\0" * 100, 16000, 1))

        def start(self, **kw):
            trace.append("audio:start")
            super().start(**kw)

        def stop(self):
            trace.append("audio:stop")
            return super().stop()

    class S:
        def transcribe(self, wav_bytes, language):
            trace.append("local-stt")
            return "ham"

    class C:
        def clean(self, text):
            trace.append("llm:clean")
            return "temiz"

    class I:
        def paste(self, text):
            trace.append("clipboard")

    recorder = R()
    controller = AppController(
        recorder,
        S(),
        C(),
        I(),
        AppSettings(),
        events=queue.Queue(),
        thread_factory=ImmediateThread,
    )

    controller.start_recording()
    controller.stop_recording()

    assert trace == ["audio:start", "audio:stop"]
    assert controller.state == AppState.READY

    controller.start_recording()

    assert recorder.starts == 2
    assert controller.state == AppState.LISTENING


def test_pipeline_logging_and_secret_redaction(tmp_path):
    import app_logger
    from audio_recorder import AudioRecorder
    from transcriber import Transcriber
    from llm_cleaner import LlmCleaner
    from text_injector import TextInjector
    import httpx

    log_file = tmp_path / "pipeline.log"
    app_logger.setup_logging(log_path=log_file)

    class MockStream:
        def __init__(self, callback): self.callback = callback
        def start(self): self.callback(b"\0\0" * 8000, 8000, None, None)
        def stop(self): pass
        def close(self): pass

    recorder = AudioRecorder(stream_factory=lambda **kw: MockStream(kw["callback"]))
    
    class MockTranscriber:
        model_name = "base"
        def transcribe(self, wav_bytes, language):
            app_logger.get_logger("transcriber").info("Transkripsiyon tamamlandı (metin=merhaba)")
            return "merhaba dünya sesli dikte"

    SECRET_KEY = "sk-9router-super-secret-key-999"
    
    def handler(request: httpx.Request):
        assert f"Bearer {SECRET_KEY}" in request.headers["Authorization"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "Merhaba dünya sesli dikte."}}]})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cleaner = LlmCleaner(base_url="https://router.erensahin.tr/v1", model="scout-flash", api_key=SECRET_KEY, client=client)

    class MockClip:
        def __init__(self): self.val = ""
        def paste(self): return self.val
        def copy(self, v): self.val = v
    class MockKey:
        def send(self, k): pass

    injector = TextInjector(MockClip(), MockKey(), sleep=lambda _: None)
    controller = AppController(recorder, MockTranscriber(), cleaner, injector, AppSettings(), events=queue.Queue(), thread_factory=ImmediateThread)

    controller.start_recording()
    controller.stop_recording()

    # Flush handlers
    import logging
    for h in logging.getLogger().handlers:
        h.flush()

    content = log_file.read_text(encoding="utf-8")
    assert SECRET_KEY not in content
    assert "Ses kaydı" in content
    assert "Transkripsiyon" in content
    assert "LLM temizleme" in content
    assert "Pipeline" in content

