import streamlit as st
import pandas as pd
import requests
import io
import re

# 1. 페이지 설정
st.set_page_config(
    page_title="Hstock V1.1 Dashboard",
    page_icon="📈",
    layout="wide"
)

# 2. 스타일링
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans KR', sans-serif; }
    .stApp { background-color: #f8fafc; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] > div { font-size: 1.8rem !important; font-weight: 700; }
    .custom-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 0.9rem; font-weight: 700; color: #64748b;
        text-transform: uppercase; margin-bottom: 16px;
        border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 파싱 함수
def parse_val(v):
    if pd.isna(v) or v == "" or v == "-": return 0.0
    s = str(v).replace(',', '').replace('원', '').replace('%', '').strip()
    s = s.replace(" ", "")
    try:
        return float(s)
    except:
        nums = re.findall(r'-?\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0

# 4. 데이터 로딩
SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=10)
def get_data():
    try:
        resp = requests.get(CSV_URL)
        resp.encoding = 'utf-8'
        return pd.read_csv(io.StringIO(resp.text), header=None)
    except Exception as e:
        return None

df = get_data()

if df is not None:
    # 종목 데이터 파싱
    dom = df.iloc[1:9, 0:10].copy()
    us = df.iloc[11:15, 0:10].copy()
    stocks = pd.concat([dom, us])
    stocks.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    stocks = stocks[stocks['Name'].notna() & (stocks['Name'].str.strip() != "")].copy()

    # 특정 키워드로 행 찾기 로직 강화
    total_row, cash_row = df.iloc[17], df.iloc[16]
    for i in range(len(df)):
        v = str(df.iloc[i, 0]).strip()
        if "Total" in v: total_row = df.iloc[i]
        if "현금" in v and i > 10: cash_row = df.iloc[i]

    # 금액 데이터 추출
    sm = {
        "eval":  parse_val(total_row[3]),
        "buy":   parse_val(total_row[4]),
        "profit": parse_val(total_row[5]),
        "rate":  str(total_row[6]),
        "daily": parse_val(total_row[7]),
        "accum": parse_val(total_row[8]),
        "cash":  parse_val(cash_row[3]),
        "total": parse_val(total_row[13]),
    }
    
    # 통계 및 날짜
    win_cnt = parse_val(df.iloc[9, 16])
    loss
