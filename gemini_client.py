import os
from typing import Callable, Optional

import requests

DEFAULT_MODEL = "gemini-2.0-flash"
LEGACY_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
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


def _is_auth_key(api_key: str) -> bool:
    return api_key.startswith("AQ.")


def _generate_with_sdk(prompt: str, *, api_key: str, model: str) -> str:
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    text = (response.text or "").strip()
    return text or "ไม่พบข้อมูล"


def _generate_with_rest(prompt: str, *, api_key: str, model: str, timeout: int) -> str:
    url = f"{LEGACY_API_BASE}/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "topP": 0.9},
    }
    headers = {"x-goog-api-key": api_key}
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates") or []
    if not candidates:
        return "ไม่พบข้อมูล"

    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    return text.strip() or "ไม่พบข้อมูล"


def generate_text(
    prompt: str,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 15,
) -> str:
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    try:
        if _is_auth_key(api_key):
            return _generate_with_sdk(prompt, api_key=api_key, model=model)
        return _generate_with_rest(prompt, api_key=api_key, model=model, timeout=timeout)
    except Exception as exc:
        message = str(exc)
        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            raise RuntimeError("Gemini quota หมดชั่วคราว — ลองใหม่ภายหลังหรือตรวจ billing") from exc
        raise