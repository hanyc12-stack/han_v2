import streamlit as st
import pandas as pd
import requests
import io

# 1. Page Configuration
st.set_page_config(
    page_title="Hstock Premium Dashboard",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Premium Styling (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0f172a;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.1), transparent),
                    #0f172a;
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    
    div[data-testid="stMetricLabel"] > div {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    div[data-testid="stMetricValue"] > div {
        color: #f8fafc !important;
        font-size: 1.5rem !important;
        font-weight: 700;
    }

    /* Dataframe Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Header */
    .header-container {
        padding: 2rem 0;
        text-align: center;
    }
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        color: #fff;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #6366f1;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 3. Data Fetching Logic
SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def get_data():
    try:
        resp = requests.get(CSV_URL)
        resp.encoding = 'utf-8'
        df_raw = pd.read_csv(io.StringIO(resp.text), header=None)
        return df_raw
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def to_int(v):
    if pd.isna(v): return 0
    try:
        return int(str(v).replace(',', '').replace('%', '').strip())
    except:
        return 0

df = get_data()

if df is not None:
    # --- Parsing Logic ---
    # Domestic Stocks (Row 2-9 -> Index 1-8)
    domestic = df.iloc[1:9, 0:10].copy()
    # US Stocks (Row 12-15 -> Index 11-14)
    us_stocks = df.iloc[11:15, 0:10].copy()
    
    stocks_raw = pd.concat([domestic, us_stocks])
    stocks_raw.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    
    # Clean Stocks Data
    stocks = stocks_raw[stocks_raw['Name'].notna() & (stocks_raw['Name'] != "현금")].copy()
    for col in ['Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice']:
        stocks[col] = stocks[col].apply(to_int)

    # Summary Data (Row 18 -> Index 17)
    row_18 = df.iloc[17]
    row_17 = df.iloc[16] # Cash row index 16 is row 17
    
    summary = {
        "total_cur":    to_int(row_18[3]),
        "total_buy":    to_int(row_18[4]),
        "profit_accum": to_int(row_18[5]),
        "rate_accum":   str(row_18[6]),
        "daily_chg":    to_int(row_18[7]),
        "accum_total":  to_int(row_18[8]),
        "total_asset":  to_int(row_18[13]),
        "cash":         to_int(row_17[3]),
        "invest_start": str(df.iloc[10, 20]), # U11
        "invest_days":  str(df.iloc[10, 22])  # W11
    }
    
    # Calculate fallback total asset
    total_asset = summary["total_asset"] if summary["total_asset"] > 0 else (summary["total_cur"] + summary["cash"])

    # Asset Allocation (Col P-R, Row 2-5 -> Index 1-4)
    assets = df.iloc[1:5, 15:18].copy()
    assets.columns = ['Name', 'Amt', 'Pct']
    assets = assets[assets['Name'].notna()]

    # UI Rendering
    st.markdown(f'<div class="header-container"><div class="main-title">{total_asset:,}원</div><div class="sub-title">총 자산 · {summary["invest_days"]}</div></div>', unsafe_allow_html=True)

    # Metrics Grid
    c1, c2 = st.columns(2)
    with c1:
        st.metric("주식 평가금액", f"{summary['total_cur']:,}원", f"매수: {summary['total_buy']:,}")
        st.metric("금일 변동액", f"{summary['daily_chg']:,}원")
    with c2:
        st.metric("누적 수익금", f"{summary['profit_accum']:,}원", summary['rate_accum'])
        st.metric("현금 보유", f"{summary['cash']:,}원")

    # Chart
    st.write("---")
    st.subheader("📊 종목별 수익금")
    chart_data = stocks[stocks['Profit'] != 0].sort_values('Profit', ascending=False)
    if not chart_data.empty:
        st.bar_chart(data=chart_data, x='Name', y='Profit', color="#6366f1")

    # Stock List
    st.write("---")
    st.subheader("📋 보유 종목 현황")
    display_df = stocks[['Name', 'Weight', 'CurPrice', 'Rate']].copy()
    display_df.columns = ['종목명', '비중', '현재가', '수익률']
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    # Asset Type
    st.write("---")
    st.subheader("🧱 자산 유형별 비중")
    for _, row in assets.iterrows():
        pct_val = float(str(row['Pct']).replace('%', '')) if pd.notna(row['Pct']) else 0
        st.write(f"{row['Name']} ({pct_val}%)")
        st.progress(min(pct_val / 100.0, 1.0))

    st.caption(f"마지막 업데이트: {summary['invest_start']} 시작 후 현재까지")

else:
    st.warning("데이터를 불러올 수 없습니다. 구글 시트 공유 설정을 확인해주세요.")
