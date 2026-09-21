import pytest
from hotkeys import HotkeyError, HotkeyService


class Backend:
    def __init__(self): self.handlers={}; self.handles={}; self.unhooked=[]; self.fail_kind=None; self.n=0
    def _add(self, kind,key,cb):
        if self.fail_kind == kind: raise RuntimeError("occupied")
        self.n+=1; handle=f"h{self.n}"; self.handlers[(kind,key)]=cb; self.handles[handle]=(kind,key,cb); return handle
    def on_press_key(self,key,cb,**kw): return self._add("down",key,cb)
    def on_release_key(self,key,cb,**kw): return self._add("up",key,cb)
    def unhook(self,h): self.unhooked.append(h)


def fire(backend, kind, key): backend.handlers[(kind,key)]()


def test_a10_toggle_down_repeat_release_then_next_down():
    b=Backend(); trace=[]; s=HotkeyService(b)
    s.register("f8","toggle",lambda:trace.append("start"),lambda:trace.append("stop"))
    fire(b,"down","f8"); fire(b,"down","f8"); fire(b,"up","f8"); fire(b,"down","f8"); fire(b,"up","f8")
    assert trace == ["start","stop"]


def test_a10_ptt_repeat_and_extra_release_are_noops():
    b=Backend(); trace=[]; s=HotkeyService(b)
    s.register("f8","push_to_talk",lambda:trace.append("start"),lambda:trace.append("stop"))
    fire(b,"down","f8"); fire(b,"down","f8"); fire(b,"up","f8"); fire(b,"up","f8")
    assert trace == ["start","stop"]


def test_a10_callback_failure_does_not_commit_state_and_recovers():
    b=Backend(); trace=[]; starts=[0]
    def start():
        starts[0]+=1
        if starts[0] == 1: raise RuntimeError("boom")
        trace.append("start")
    s=HotkeyService(b); s.register("f8","toggle",start,lambda:trace.append("stop"))
    fire(b,"down","f8"); fire(b,"up","f8"); fire(b,"down","f8"); fire(b,"up","f8")
    assert trace == ["start"]
    fire(b,"down","f8"); fire(b,"up","f8")
    assert trace == ["start", "stop"]


def test_a10_partial_reregister_failure_keeps_old_two_handlers():
    b=Backend(); trace=[]; s=HotkeyService(b)
    s.register("f8","push_to_talk",lambda:trace.append("old-start"),lambda:trace.append("old-stop"))
    old_down=b.handlers[("down","f8")]; old_up=b.handlers[("up","f8")]
    b.fail_kind="up"
    with pytest.raises(HotkeyError): s.register("f9","push_to_talk",lambda:trace.append("new"),lambda:None)
    old_down(); old_up()
    assert trace == ["old-start", "old-stop"]
    assert "h3" in b.unhooked and "h1" not in b.unhooked and "h2" not in b.unhooked
