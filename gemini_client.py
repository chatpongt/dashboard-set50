import os
from typing import Callable, Optional

import requests

DEFAULT_MODEL = "gemini-2.0-flash"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
API_KEY_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY")


def _resolve(get_secret: Optional[Callable[[str], str]], key: str) -> str:
    if get_secret:
        try:
            value = get_secret(key)
            if value:
                return value
        except Exception:
            pass
    return os.getenv(key, "")


def get_api_key(get_secret: Optional[Callable[[str], str]] = None) -> str:
    for name in API_KEY_NAMES:
        value = _resolve(get_secret, name)
        if value:
            return value
    return ""


def get_model(get_secret: Optional[Callable[[str], str]] = None) -> str:
    return _resolve(get_secret, "GEMINI_MODEL") or DEFAULT_MODEL


def generate_text(
    prompt: str,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 15,
) -> str:
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    url = f"{API_BASE}/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "topP": 0.9},
    }
    resp = requests.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates") or []
    if not candidates:
        return "ไม่พบข้อมูล"

    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    return text.strip() or "ไม่พบข้อมูล"