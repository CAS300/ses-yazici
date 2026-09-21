import httpx
import pytest

from llm_cleaner import CleaningError, DICTATION_SYSTEM_PROMPT, LlmCleaner


def test_payload_separates_system_and_user_and_returns_content():
    captured = {}
    def handler(request):
        captured["request"] = request
        return httpx.Response(200, json={"choices": [{"message": {"content": "Düzeltilmiş metin."}}]})
    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = LlmCleaner("https://router.test/v1/", "scout-flash", "opaque", client).clean("ııı ham metin")
    import json
    request = captured["request"]; payload = json.loads(request.content)
    assert str(request.url) == "https://router.test/v1/chat/completions"
    assert payload["model"] == "scout-flash" and payload["temperature"] == 0
    assert payload["messages"] == [{"role": "system", "content": DICTATION_SYSTEM_PROMPT}, {"role": "user", "content": "ııı ham metin"}]
    assert result == "Düzeltilmiş metin."


@pytest.mark.parametrize("response", [
    httpx.Response(500), httpx.Response(200, content=b"not-json"),
    httpx.Response(200, json={}),
    httpx.Response(200, json={"choices": [{"message": {"content": " "}}]}),
])
def test_fault_matrix(response):
    client = httpx.Client(transport=httpx.MockTransport(lambda r: response))
    with pytest.raises(CleaningError): LlmCleaner("https://x.test/v1", "ulku", "opaque", client).clean("raw")


def test_raw_text_not_logged(caplog):
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    with pytest.raises(CleaningError): LlmCleaner("https://x.test/v1", "ulku", "opaque", client).clean("private transcript")
    assert "private transcript" not in caplog.text and "opaque" not in caplog.text
