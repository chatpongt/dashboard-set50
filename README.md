# 📊 SET50 Dashboard

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=chatpongt/dashboard-set50&branch=main&mainModule=app.py)

แอปวิเคราะห์หุ้นไทย SET50 แบบ real-time — Sentiment + Valuation

**Live:** https://chatpongt-dashboard-set50.streamlit.app/

---

## Pages

| หน้า | รายละเอียด |
|------|-----------|
| 🏠 Sentiment Dashboard | วิเคราะห์ sentiment ด้วย Perplexity Sonar AI |
| 📊 Valuation Dashboard | Valuation Sheet 100+ หุ้น 22 sectors พร้อม charts และ daily auto-refresh |

## Deploy (1 คลิก)

1. ไปที่ [share.streamlit.io](https://share.streamlit.io)
2. **New app** → เลือก repo `chatpongt/dashboard-set50` → branch `main` → main file `app.py`
3. ใส่ secrets ใน **Advanced settings**:

```toml
# จำเป็น
PERPLEXITY_API_KEY = "pplx-..."

# Valuation auto-refresh (optional)
VALUATION_GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/..."

# Supabase — เก็บประวัติการวิเคราะห์ (optional)
SUPABASE_URL      = "https://<ref>.supabase.co"
SUPABASE_ANON_KEY = "eyJ..."

# Resend — ส่งรายงานทางอีเมล (optional)
RESEND_API_KEY = "re_..."
RESEND_FROM    = "onboarding@resend.dev"
```

4. กด **Deploy** → ได้ URL ภายใน 1–2 นาที

---

## Local Setup

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# แก้ไข secrets.toml ใส่ API keys
streamlit run app.py
```

## Supabase Schema

รัน `supabase/schema.sql` ใน Supabase SQL Editor ก่อนใช้งาน

## Dynamic Valuation Data

ตั้งค่า `VALUATION_GSHEET_CSV_URL` เพื่อดึงข้อมูลจาก Google Sheets อัตโนมัติทุก 24 ชม.

วิธีเตรียม CSV URL:
1. เปิด Google Sheet → **File → Share → Publish to web**
2. เลือก tab valuation → format **CSV** → **Publish**
3. Copy URL → ใส่ใน secrets.toml
