import pytest
from hotkeys import HotkeyError, HotkeyService


class Backend:
    def __init__(self): self.handlers={}; self.unhooked=[]; self.fail=False; self.n=0
    def _add(self, kind,key,cb):
        if self.fail: raise RuntimeError("occupied")
        self.n+=1; handle=f"h{self.n}"; self.handlers[(kind,key)]=cb; return handle
    def add_hotkey(self,key,cb,**kw): return self._add("toggle",key,cb)
    def on_press_key(self,key,cb,**kw): return self._add("down",key,cb)
    def on_release_key(self,key,cb,**kw): return self._add("up",key,cb)
    def unhook(self,h): self.unhooked.append(h)


def test_toggle_trace():
    b=Backend(); trace=[]; s=HotkeyService(b); s.register("f8","toggle",lambda:trace.append("start"),lambda:trace.append("stop"))
    b.handlers[("toggle","f8")](); b.handlers[("toggle","f8")]()
    assert trace == ["start","stop"]


def test_ptt_repeat_only_one_start_and_release_stop():
    b=Backend(); trace=[]; s=HotkeyService(b); s.register("f8","push_to_talk",lambda:trace.append("start"),lambda:trace.append("stop"))
    b.handlers[("down","f8")](); b.handlers[("down","f8")](); b.handlers[("up","f8")](); b.handlers[("up","f8")]()
    assert trace == ["start","stop"]


def test_failed_reregister_keeps_old_binding():
    b=Backend(); trace=[]; s=HotkeyService(b); s.register("f8","toggle",lambda:trace.append("old"),lambda:None)
    b.fail=True
    with pytest.raises(HotkeyError): s.register("f9","toggle",lambda:trace.append("new"),lambda:None)
    b.handlers[("toggle","f8")](); assert trace == ["old"] and b.unhooked == []
