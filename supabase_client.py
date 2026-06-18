import os
import streamlit as st

def _get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key, "")

def _get_client():
    from supabase import create_client
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def save_analysis(results: list) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        rows = [
            {
                "stock": r["หุ้น"],
                "sentiment_score": r["Sentiment Score"],
                "signal": r["สัญญาณ"],
                "summary": r["สรุปข่าว"],
            }
            for r in results
        ]
        client.table("sentiment_analyses").insert(rows).execute()
        return True
    except Exception:
        return False

def get_history(limit: int = 30) -> list:
    client = _get_client()
    if not client:
        return []
    try:
        res = (
            client.table("sentiment_analyses")
            .select("stock, sentiment_score, signal, analyzed_at")
            .order("analyzed_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def is_configured() -> bool:
    return bool(_get_secret("SUPABASE_URL") and _get_secret("SUPABASE_ANON_KEY"))
