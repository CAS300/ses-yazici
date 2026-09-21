import io
import wave

import pytest

from audio_recorder import AudioClip, AudioError, AudioRecorder, encode_wav


class Stream:
    def __init__(self, **kwargs): self.callback = kwargs["callback"]; self.started = self.stopped = self.closed = False
    def start(self): self.started = True
    def stop(self): self.stopped = True
    def close(self): self.closed = True


def test_wav_header_and_metadata():
    data = encode_wav(AudioClip(b"\x01\x00" * 160, 16000, 1))
    with wave.open(io.BytesIO(data), "rb") as wav:
        assert (wav.getnchannels(), wav.getframerate(), wav.getsampwidth(), wav.getnframes()) == (1, 16000, 2, 160)
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"


def test_recorder_stream_state_and_duration_cap():
    streams = []
    def factory(**kwargs): streams.append(Stream(**kwargs)); return streams[-1]
    recorder = AudioRecorder(factory, max_record_seconds=1)
    recorder.start()
    streams[0].callback(b"x" * 40000, 20000, None, None)
    clip = recorder.stop()
    assert len(clip.pcm_s16le) == 32000
    assert streams[0].started and streams[0].stopped and streams[0].closed
    assert not recorder.is_recording


def test_double_start_and_cancel():
    recorder = AudioRecorder(lambda **kw: Stream(**kw))
    recorder.start()
    with pytest.raises(AudioError): recorder.start()
    recorder.cancel(); assert not recorder.is_recording
