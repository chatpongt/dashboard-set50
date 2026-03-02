import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import os

st.set_page_config(page_title="SET50 Sentiment Dashboard", layout="wide")

# --- Config ---
STOCKS = ['ADVANC', 'AOT', 'PTTEP', 'PTT', 'SCB', 'KBANK', 'BBL', 'CPALL', 'SCC', 'DELTA']
API_KEY = st.secrets.get("PERPLEXITY_API_KEY", os.getenv("PERPLEXITY_API_KEY", ""))
API_URL = "https://api.perplexity.ai/chat/completions"

# --- Functions ---
def get_sentiment(stock):
    if not API_KEY or API_KEY == "":
        return f"[Demo] หุ้น {stock} — กรุณาตั้งค่า PERPLEXITY_API_KEY"
    query = f"สรุปข่าวและ sentiment หุ้น {stock} วันนี้ (ภาษาไทยสั้นๆ)"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": query}],
        "temperature": 0.2,
        "top_p": 0.9
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "ไม่พบข้อมูล")
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
st.caption("วิเคราะห์ sentiment หุ้นไทย real-time ด้วย Perplexity AI")

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
    color_map = {1: '#00cc44', 0: '#aaaaaa', -1: '#ff4444'}
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

elif not run:
    st.info("👆 เลือกหุ้นแล้วกดปุ่ม **วิเคราะห์ Sentiment** ด้านบน")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ การตั้งค่า")
    st.markdown("**Perplexity API Key**")
    if not API_KEY:
        st.warning("ยังไม่ได้ตั้งค่า API Key\nไปที่ Streamlit Secrets แล้วเพิ่ม:\n```\nPERPLEXITY_API_KEY = 'your_key'\n```")
    else:
        st.success("API Key พร้อมใช้งาน ✅")
    st.markdown("---")
    st.caption("หุ้นที่รองรับ: SET50")
    st.caption("Model: Perplexity Sonar")
