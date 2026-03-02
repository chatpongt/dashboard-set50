# 📊 SET50 Sentiment Dashboard

วิเคราะห์ sentiment หุ้นไทย real-time ด้วย Perplexity AI

## Features
- เลือกหุ้น SET50 ได้หลายตัว
- วิเคราะห์ข่าวและ sentiment ด้วย Perplexity Sonar
- Bar chart สรุป Positive / Neutral / Negative
- สรุปข่าวรายหุ้น

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## API Key
ตั้งค่า Perplexity API Key ใน `.streamlit/secrets.toml`:
```toml
PERPLEXITY_API_KEY = "your_key_here"
```
