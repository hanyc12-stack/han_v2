import streamlit as st
import pandas as pd
import requests
import io

# 1. Page Configuration
st.set_page_config(
    page_title="Hstock V1.1 Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Light Mode Aesthetic Styling (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
        background-color: #f1f5f9;
        color: #1e293b;
    }
    
    .stApp {
        background-color: #f8fafc;
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    div[data-testid="stMetricLabel"] > div {
        color: #64748b !important;
        font-size: 0.85rem !important;
        font-weight: 500;
        margin-bottom: 8px;
    }
    
    div[data-testid="stMetricValue"] > div {
        color: #0f172a !important;
        font-size: 1.6rem !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Container Card */
    .custom-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .card-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 16px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
    }

    /* Header Styling */
    .header-section {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        padding: 20px 0 30px 0;
    }
    .total-asset-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .total-asset-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.03em;
    }
    .invest-info {
        text-align: right;
        color: #64748b;
    }
    .invest-date {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1e293b;
    }

    /* Dataframe & Progress */
    .stDataFrame { border: none !important; }
    
    /* UTILS */
    .up { color: #10b981 !important; }
    .down { color: #ef4444 !important; }
    .muted { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# 3. Data Fetching
SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=60)
def get_data():
    try:
        resp = requests.get(CSV_URL)
        resp.encoding = 'utf-8'
        df_raw = pd.read_csv(io.StringIO(resp.text), header=None)
        return df_raw
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류 발생: {e}")
        return None

def parse(v):
    if pd.isna(v): return 0
    s = str(v).replace(',', '').replace('%', '').replace('원', '').strip()
    try:
        return float(s) if '.' in s else int(s)
    except:
        return 0

df = get_data()

if df is not None:
    # --- 정확한 인덱스 매핑 (V1.1 기준) ---
    # 1. 종목 데이터 (Domestic: 2-9행, US: 12-15행)
    domestic = df.iloc[1:9, 0:10].copy()
    us_stocks = df.iloc[11:15, 0:10].copy()
    stocks_raw = pd.concat([domestic, us_stocks])
    stocks_raw.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    
    stocks = stocks_raw[stocks_raw['Name'].notna() & (stocks_raw['Name'] != "현금")].copy()
    for col in ['Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice']:
        stocks[col] = stocks[col].apply(parse)

    # 2. 요약 데이터 (Row 18)
    row_18 = df.iloc[17]
    row_17 = df.iloc[16] # Cash row index 16 is row 17
    
    # 통계 데이터 (Winning/Losing - Row 10, Q10, R10)
    win_cnt = parse(df.iloc[9, 16]) # Q10
    loss_cnt = parse(df.iloc[9, 17]) # R10
    total_cnt = len(stocks)
    
    # 투자 정보 (Start Date - P16, Days - R16)
    invest_start = str(df.iloc[15, 15]) if not pd.isna(df.iloc[15, 15]) else "2023.10.15"
    invest_days = str(df.iloc[15, 17]) if not pd.isna(df.iloc[15, 17]) else "0일"

    summary = {
        "total_cur":    parse(row_18[3]),
        "total_buy":    parse(row_18[4]),
        "profit_accum": parse(row_18[5]),
        "rate_accum":   str(row_18[6]),
        "daily_chg":    parse(row_18[7]),
        "accum_total":  parse(row_18[8]), # 누적 총수익
        "total_asset":  parse(row_18[13]),
        "cash":         parse(row_17[3]),
    }
    
    # 총자산 보정
    total_asset = summary["total_asset"] if summary["total_asset"] > 0 else (summary["total_cur"] + summary["cash"])

    # 3. UI 렌더링
    
    # Top Header
    st.markdown(f"""
    <div class="header-section">
        <div>
            <div class="total-asset-label">총 자산 (Hstock V1.1)</div>
            <div class="total-asset-value">{int(total_asset):,}원</div>
        </div>
        <div class="invest-info">
            <div>투자 시작일</div>
            <div class="invest-date">{invest_start} | <span style="color:#6366f1">{invest_days}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics Row 1
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("주식 평가금액", f"{int(summary['total_cur']):,}원")
    with m2: st.metric("매수금액", f"{int(summary['total_buy']):,}원")
    with m3: st.metric("누적 수익금", f"{int(summary['profit_accum']):,}원", summary['rate_accum'])
    with m4: st.metric("금일 변동액", f"{int(summary['daily_chg']):+,}원")

    # Metrics Row 2
    m5, m6, m7, m8 = st.columns(4)
    with m5: st.metric("총 종목수", f"{total_cnt}종목")
    with m6: 
        win_pct = (win_cnt / total_cnt * 100) if total_cnt > 0 else 0
        st.metric("수익 종목", f"{int(win_cnt)}", f"{win_pct:.1f}%", delta_color="normal")
    with m7: 
        loss_pct = (loss_cnt / total_cnt * 100) if total_cnt > 0 else 0
        st.metric("손실 종목", f"{int(loss_cnt)}", f"-{loss_pct:.1f}%", delta_color="inverse")
    with m8: st.metric("누적 총수익", f"{int(summary['accum_total']):,}원")

    st.write("") # Spacer

    # Main Content Area
    col_left, col_right = st.columns([2.2, 1])

    with col_left:
        st.markdown('<div class="custom-card"><div class="card-title">보유 종목 현황</div>', unsafe_allow_html=True)
        # 테이블 데이터 다듬기
        tbl_df = stocks[['Name', 'Weight', 'CurPrice', 'AvgPrice', 'Rate']].copy()
        tbl_df.columns = ['종목명', '비중', '현재가', '평단가', '수익률']
        
        # 스타일링된 테이블 출력
        st.dataframe(
            tbl_df.style.format({
                '현재가': '{:,.0f}',
                '평단가': '{:,.0f}'
            }), 
            hide_index=True, 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # 차트 (좌측 하단)
        st.markdown('<div class="custom-card"><div class="card-title">종목별 수익금 비교</div>', unsafe_allow_html=True)
        chart_data = stocks[stocks['Profit'] != 0].sort_values('Profit', ascending=False)
        if not chart_data.empty:
            # 막대 차트
            st.bar_chart(data=chart_data, x='Name', y='Profit', color="#6366f1")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # 자산 비중 (우측)
        st.markdown('<div class="custom-card"><div class="card-title">자산 유형별 비중</div>', unsafe_allow_html=True)
        assets = df.iloc[1:5, 15:18].copy()
        assets.columns = ['Name', 'Amt', 'Pct']
        assets = assets[assets['Name'].notna()]
        for _, row in assets.iterrows():
            p_val = parse(row['Pct'])
            st.write(f"**{row['Name']}** <span style='float:right; color:#64748b;'>{p_val}%</span>", unsafe_allow_html=True)
            st.progress(min(p_val / 100.0, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)

        # 증권사 비중
        st.markdown('<div class="custom-card"><div class="card-title">증권사별 비중</div>', unsafe_allow_html=True)
        brokers = df.iloc[1:15, 11:14].copy()
        brokers.columns = ['Name', 'Pct', 'Amt']
        brokers = brokers[brokers['Name'].notna() & (brokers['Name'] != "증권사")]
        for _, row in brokers.iterrows():
            p_val = parse(row['Pct'])
            st.write(f"**{row['Name']}** <span style='float:right; color:#64748b;'>{p_val}%</span>", unsafe_allow_html=True)
            st.progress(min(p_val / 100.0, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)

        # 현금 보유량
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.metric("현금 보유", f"{int(summary['cash']):,}원")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<div style='text-align:center; padding:20px; color:#94a3b8; font-size:0.8rem;'>마지막 동기화: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)

else:
    st.warning("데이터를 불러올 수 없습니다. 구글 시트 공유 설정을 확인해주세요.")
