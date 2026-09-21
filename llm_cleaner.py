from __future__ import annotations

import time

import httpx

from app_logger import get_logger
from settings import api_url

logger = get_logger("llm_cleaner")

DICTATION_SYSTEM_PROMPT = (
    "Sen bir dikte asistanısın. Kullanıcının konuşma dilindeki dolgu seslerini "
    "('ııı', 'eee', 'şey', duraksamalar) temizle. Dağınık cümleleri anlamı "
    "kesinlikle değiştirmeden akıcı, kurallı ve düzgün cümleler haline getir. "
    "Yalnızca düzeltilmiş nihai metni döndür, tırnak veya açıklama ekleme."
)


class CleaningError(RuntimeError):
    pass


class LlmCleaner:
    def __init__(self, base_url: str, model: str, api_key: str, client: httpx.Client):
        self.url = api_url(base_url, "v1/chat/completions")
        self.model = model
        self.api_key = api_key
        self.client = client

    def clean(self, raw_text: str) -> str:
        if not raw_text.strip():
            logger.warning("Temizlenecek metin boş.")
            raise CleaningError("Temizlenecek metin boş.")
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": DICTATION_SYSTEM_PROMPT},
                {"role": "user", "content": raw_text},
            ],
        }
        logger.info("LLM temizleme isteği gönderiliyor (model=%s, url=%s, metin_uzunluğu=%d)", self.model, self.url, len(raw_text))
        start_time = time.perf_counter()
        try:
            response = self.client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=45.0,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info("LLM temizleme tamamlandı (süre=%.1f ms, dönen_uzunluk=%d)", elapsed_ms, len(content) if isinstance(content, str) else 0)
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            logger.error("LLM temizleme servisi hatası: %s", exc)
            raise CleaningError("Metin düzenleme servisi yanıt vermedi.") from exc
        if not isinstance(content, str) or not content.strip():
            raise CleaningError("Metin düzenleme servisi boş yanıt verdi.")
        return content.strip()
