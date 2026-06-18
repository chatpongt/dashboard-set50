import os
import streamlit as st

def _get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key, "")

def _build_html(results: list) -> str:
    rows_html = ""
    for r in results:
        score = r["Sentiment Score"]
        color = "#00cc44" if score > 0 else "#ff4444" if score < 0 else "#888888"
        summary = r["สรุปข่าว"]
        short = summary[:250] + "…" if len(summary) > 250 else summary
        rows_html += f"""
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #eee;font-weight:600;white-space:nowrap">
                {r['หุ้น']}
            </td>
            <td style="padding:10px 12px;border-bottom:1px solid #eee;color:{color};font-weight:600;white-space:nowrap">
                {r['สัญญาณ']}
            </td>
            <td style="padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;color:#444;line-height:1.5">
                {short}
            </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:'Helvetica Neue',Arial,sans-serif">
  <div style="max-width:720px;margin:32px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
    <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:32px 36px">
      <h1 style="margin:0;color:#fff;font-size:24px">📊 SET50 Sentiment Report</h1>
      <p style="margin:8px 0 0;color:#a0b4d0;font-size:14px">วิเคราะห์ sentiment หุ้นไทย real-time ด้วย Perplexity AI</p>
    </div>
    <div style="padding:28px 36px">
      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="background:#f8f9fa">
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:0.5px">หุ้น</th>
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:0.5px">สัญญาณ</th>
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:0.5px">สรุปข่าว</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <div style="padding:20px 36px 28px;border-top:1px solid #eee">
      <p style="margin:0;color:#aaa;font-size:12px">
        Powered by Perplexity Sonar · SET50 Sentiment Dashboard
      </p>
    </div>
  </div>
</body>
</html>"""

def send_report(to_email: str, results: list) -> bool:
    import resend
    api_key = _get_secret("RESEND_API_KEY")
    if not api_key:
        return False
    resend.api_key = api_key
    from_addr = _get_secret("RESEND_FROM") or "onboarding@resend.dev"
    try:
        resend.Emails.send({
            "from": f"SET50 Dashboard <{from_addr}>",
            "to": [to_email],
            "subject": "📊 SET50 Sentiment Report",
            "html": _build_html(results),
        })
        return True
    except Exception:
        return False

def is_configured() -> bool:
    return bool(_get_secret("RESEND_API_KEY"))
