import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import requests
import os

STOCKS = ['ADVANC', 'AOT', 'PTTEP', 'PTT', 'SCB']
API_KEY = os.getenv("PERPLEXITY_API_KEY", "YOUR_API_KEY")
API_URL = "https://api.perplexity.ai/chat/completions"

def get_sentiment(stock):
    query = (
        f"สรุปข่าวและ sentiment หุ้น {stock} วันนี้ (ภาษาไทยสั้นๆ)"
    )
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
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=12)
        result = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return result
    except Exception:
        return "ข้อมูลผิดพลาด"

def score(text):
    pos = ['บวก','ดี','เพิ่ม','ฟื้นตัว','กำไร']
    neg = ['ลบ','ลด','แย่','ขาดทุน','ซบเซา']
    s = sum(1 for p in pos if p in text) - sum(1 for n in neg if n in text)
    return 1 if s > 0 else -1 if s < 0 else 0

def latest_sentiments():
    df = []
    for stock in STOCKS:
        sent = get_sentiment(stock)
        df.append({'Stock': stock, 'Sentiment': score(sent), 'Summary': sent})
    return pd.DataFrame(df)

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H3("SET50 Sentiment Dashboard (Realtime)"),
    dcc.Dropdown(
        id="stock",
        options=[{"label": s, "value": s} for s in STOCKS],
        value=STOCKS[0]
    ),
    html.Button("Refresh", id="refresh"),
    dcc.Graph(id="bar"),
    html.Div(id="summary")
])

@app.callback(
    Output("bar", "figure"),
    Output("summary", "children"),
    Input("refresh", "n_clicks"),
    Input("stock", "value")
)
def update(n, selected_stock):
    df = latest_sentiments()
    fig = px.bar(df, x='Stock', y='Sentiment', color='Sentiment',
                 color_continuous_scale=['red', 'gray', 'green'])
    text = df[df['Stock'] == selected_stock]['Summary'].values[0]
    return fig, f"สรุปสำหรับ {selected_stock}: {text}"

if __name__ == '__main__':
    app.run(debug=True)
