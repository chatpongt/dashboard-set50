import streamlit as st
import plotly.express as px
import pandas as pd
import os

import gemini_client
import supabase_client
import email_service

st.set_page_config(page_title="SET50 Sentiment Dashboard", layout="wide")

# --- Config ---
STOCKS = ['ADVANC', 'AOT', 'PTTEP', 'PTT', 'SCB', 'KBANK', 'BBL', 'CPALL', 'SCC', 'DELTA']

def _get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key, "")

API_KEY = gemini_client.get_api_key(_get_secret)
GEMINI_MODEL = gemini_client.get_model(_get_secret)

# --- Functions ---
def get_sentiment(stock):
    if not API_KEY:
        return f"[Demo] หุ้น {stock} — กรุณาตั้งค่า GEMINI_API_KEY"
    query = f"สรุปข่าวและ sentiment หุ้น {stock} วันนี้ (ภาษาไทยสั้นๆ)"
    try:
        return gemini_client.generate_text(
            query,
            api_key=API_KEY,
            model=GEMINI_MODEL,
            timeout=15,
        )
    except Exception as e:
        return f"ข้อมูลผิดพลาด: {e}"

def score(text):
    pos = ['บวก', 'ดี', 'เพิ่ม', 'ฟื้นตัว', 'กำไร', 'ขึ้น', 'แข็งแกร่ง']
    neg = ['ลบ', 'ลด', 'แย่', 'ขาดทุน', 'ซบเซา', 'ลง', 'ร่วง', 'กังวล']
    s = sum(1 for p in pos if p in text) - sum(1 for n in neg if n in text)
    return 1 if s > 0 else -1 if s < 0 else 0

def score_label(s):
    return "🟢 Positive" if s > 0 else "🔴 Negative" if s < 0 else "⚪ Neutral"

# --- UI ---
st.title("📊 SET50 Sentiment Dashboard")
st.caption("วิเคราะห์ sentiment หุ้นไทย real-time ด้วย Google Gemini")

col1, col2 = st.columns([2, 1])

with col1:
    selected_stocks = st.multiselect(
        "เลือกหุ้นที่ต้องการวิเคราะห์",
        options=STOCKS,
        default=['ADVANC', 'AOT', 'PTT', 'KBANK', 'SCB']
    )

with col2:
    st.write("")
    st.write("")
    run = st.button("🔄 วิเคราะห์ Sentiment", type="primary", use_container_width=True)

if run and selected_stocks:
    with st.spinner("กำลังดึงข่าวและวิเคราะห์ sentiment..."):
        rows = []
        for stock in selected_stocks:
            summary = get_sentiment(stock)
            s = score(summary)
            rows.append({
                'หุ้น': stock,
                'Sentiment Score': s,
                'สัญญาณ': score_label(s),
                'สรุปข่าว': summary
            })
        df = pd.DataFrame(rows)

    # --- Chart ---
    st.subheader("📈 Sentiment Overview")
    fig = px.bar(
        df, x='หุ้น', y='Sentiment Score',
        color='Sentiment Score',
        color_continuous_scale=['#ff4444', '#aaaaaa', '#00cc44'],
        range_color=[-1, 1],
        text='สัญญาณ',
        height=400
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        showlegend=False,
        yaxis=dict(tickvals=[-1, 0, 1], ticktext=['Negative', 'Neutral', 'Positive']),
        xaxis_title="", yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Summary Cards ---
    st.subheader("📰 สรุปรายหุ้น")
    for _, row in df.iterrows():
        with st.expander(f"{row['หุ้น']} — {row['สัญญาณ']}"):
            st.write(row['สรุปข่าว'])

    # --- Table ---
    st.subheader("📋 ตารางสรุป")
    st.dataframe(
        df[['หุ้น', 'สัญญาณ', 'สรุปข่าว']],
        use_container_width=True,
        hide_index=True
    )

    # --- Save to Supabase ---
    if supabase_client.is_configured():
        saved = supabase_client.save_analysis(rows)
        if saved:
            st.toast("💾 บันทึกผลลัพธ์ลง Supabase แล้ว", icon="✅")

    # --- Send email via Resend ---
    notify_email = st.session_state.get("notify_email", "")
    if notify_email and email_service.is_configured():
        with st.spinner("กำลังส่งอีเมลรายงาน..."):
            sent = email_service.send_report(notify_email, rows)
        if sent:
            st.toast(f"📧 ส่งรายงานไปที่ {notify_email} แล้ว", icon="✅")
        else:
            st.toast("ส่งอีเมลไม่สำเร็จ กรุณาตรวจสอบ RESEND_API_KEY", icon="⚠️")

elif not run:
    st.info("👆 เลือกหุ้นแล้วกดปุ่ม **วิเคราะห์ Sentiment** ด้านบน")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ การตั้งค่า")

    # API Keys status
    st.markdown("**Gemini API**")
    if not API_KEY:
        st.warning("ยังไม่ได้ตั้งค่า `GEMINI_API_KEY`")
    else:
        st.success(f"Gemini พร้อมใช้งาน ✅ ({GEMINI_MODEL})")

    st.markdown("**Supabase**")
    if supabase_client.is_configured():
        st.success("Supabase เชื่อมต่อแล้ว ✅")
    else:
        st.info("ยังไม่ได้ตั้งค่า `SUPABASE_URL` / `SUPABASE_ANON_KEY`")

    st.markdown("**Email (Resend)**")
    if email_service.is_configured():
        st.success("Resend พร้อมใช้งาน ✅")
        notify = st.text_input(
            "ส่งรายงานไปยังอีเมล",
            placeholder="you@example.com",
            key="notify_email"
        )
    else:
        st.info("ยังไม่ได้ตั้งค่า `RESEND_API_KEY`")

    st.markdown("---")

    # History from Supabase
    if supabase_client.is_configured():
        st.markdown("**📜 ประวัติการวิเคราะห์**")
        history = supabase_client.get_history(limit=30)
        if history:
            hist_df = pd.DataFrame(history)
            hist_df["analyzed_at"] = pd.to_datetime(hist_df["analyzed_at"]).dt.strftime("%d/%m %H:%M")
            hist_df = hist_df.rename(columns={
                "stock": "หุ้น",
                "signal": "สัญญาณ",
                "analyzed_at": "เวลา"
            })
            st.dataframe(
                hist_df[["เวลา", "หุ้น", "สัญญาณ"]],
                use_container_width=True,
                hide_index=True,
                height=300
            )
        else:
            st.caption("ยังไม่มีประวัติการวิเคราะห์")

    st.markdown("---")
    st.caption("หุ้นที่รองรับ: SET50")
    st.caption(f"Model: {GEMINI_MODEL}")
