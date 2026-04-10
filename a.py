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
)import streamlit as st
import pandas as pd
import requests
import io
import re

# 1. Page Configuration
st.set_page_config(
    page_title="Hstock V1.1 Dashboard",
    page_icon="📈",
    layout="wide"
)

# 2. Styling (Light Mode & Premium Polish)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    div[data-testid="stMetricValue"] > div {
        font-size: 1.8rem !important;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

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
        margin-bottom: 16px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
    }

    /* Main Asset Header */
    .hero-section {
        padding: 20px 0 40px 0;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    .hero-label { font-size: 0.9rem; color: #64748b; font-weight: 600; margin-bottom: 4px; }
    .hero-value { font-size: 3rem; font-weight: 800; color: #0f172a; letter-spacing: -0.03em; line-height: 1; }
    .hero-right { text-align: right; color: #64748b; }
    .hero-days { font-size: 1.2rem; font-weight: 700; color: #6366f1; }
</style>
""", unsafe_allow_html=True)

# 3. Data Engine
def parse_numeric(v):
    if pd.isna(v) or v == "" or v == "-": return 0.0
    s = str(v).replace(',', '').replace('원', '').replace('%', '').strip()
    s = s.replace(" ", "")
    try:
        return float(s)
    except:
        nums = re.findall(r'-?\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0

# Correct GID for '대시보드' sheet
SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg"
GID = "1550923272" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=15)
def fetch_sheet_data():
    try:
        # User requested to reference up to column VZ (very wide)
        resp = requests.get(CSV_URL)
        resp.encoding = 'utf-8'
        return pd.read_csv(io.StringIO(resp.text), header=None)
    except Exception as e:
        return None

df = fetch_sheet_data()

if df is not None:
    # --- Precise Index Mapping (0-based indexing) ---
    
    # Stock Tables
    domestic_table = df.iloc[1:9, 0:10].copy() # Row 2-9
    us_table = df.iloc[11:15, 0:10].copy()      # Row 12-15
    stocks_raw = pd.concat([domestic_table, us_table])
    stocks_raw.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    stocks = stocks_raw[stocks_raw['Name'].notna() & (stocks_raw['Name'].str.strip() != "")].copy()

    # Summary Row (Row 18 -> Index 17)
    row_sub_total = df.iloc[16] # Row 17 (Cash row)
    row_total = df.iloc[17]     # Row 18 (Total row)
    
    # Stats (Row 8 -> Index 7)
    total_cnt = parse_numeric(df.iloc[7, 15]) # P8
    win_cnt = parse_numeric(df.iloc[7, 16])   # Q8
    loss_cnt = parse_numeric(df.iloc[7, 17])  # R8
    
    # Invest Info (Row 11 -> Index 10)
    invest_start = str(df.iloc[10, 16]) if not pd.isna(df.iloc[10, 16]) else "2023.10.15" # Q11
    invest_days = str(df.iloc[10, 17]) if not pd.isna(df.iloc[10, 17]) else "0일"         # R11

    # Main Metrics Mapping
    sm = {
        "eval":  parse_numeric(row_total[3]),  # D18
        "buy":   parse_numeric(row_total[4]),  # E18
        "profit": parse_numeric(row_total[5]), # F18
        "rate":  str(row_total[6]),            # G18
        "daily": parse_numeric(row_total[7]),  # H18
        "accum": parse_numeric(row_total[8]),  # I18
        "cash":  parse_numeric(row_sub_total[3]), # D17
        "total": parse_numeric(row_total[13]), # N18 (Total Asset)
    }
    
    # Fallback for Total Asset if Col N is empty
    real_total = sm["total"] if sm["total"] > 0 else (sm["eval"] + sm["cash"])

    # UI Rendering
    st.markdown(f"""
    <div class="hero-section">
        <div>
            <div class="hero-label">총 자산 (Hstock V1.1)</div>
            <div class="hero-value">{int(real_total):,}원</div>
        </div>
        <div class="hero-right">
            <div style="font-size:0.85rem; margin-bottom:4px;">투자 시작일: {invest_start}</div>
            <div class="hero-days">{invest_days} 경과</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics Grid
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("주식 평가금액", f"{int(sm['eval']):,}원")
    m2.metric("매수금액", f"{int(sm['buy']):,}원")
    m3.metric("누적 수익금", f"{int(sm['profit']):,}원", sm['rate'])
    m4.metric("금일 변동액", f"{int(sm['daily']):+,}원")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("총 종목수", f"{int(total_cnt)}종목")
    w_p = (win_cnt/total_cnt*100) if total_cnt>0 else 0
    m6.metric("수익 종목", f"{int(win_cnt)}", f"{w_p:.1f}%")
    l_p = (loss_cnt/total_cnt*100) if total_cnt>0 else 0
    m7.metric("손실 종목", f"{int(loss_cnt)}", f"-{l_p:.1f}%", delta_color="inverse")
    m8.metric("누적 총수익", f"{int(sm['accum']):,}원")

    st.write("") 

    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown('<div class="custom-card"><div class="card-title">보유 종목 현황</div>', unsafe_allow_html=True)
        # Table with AvgPrice
        t_df = stocks[['Name', 'Weight', 'CurPrice', 'AvgPrice', 'Rate']].copy()
        t_df.columns = ['종목명', '비중', '현재가', '평단가', '수익률']
        st.dataframe(t_df, hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="custom-card"><div class="card-title">종목별 수익금 현황</div>', unsafe_allow_html=True)
        c_data = stocks[stocks['Profit'] != 0].copy()
        c_data['Profit'] = c_data['Profit'].apply(parse_numeric)
        st.bar_chart(data=c_data, x='Name', y='Profit', color="#6366f1")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="custom-card"><div class="card-title">자산 유형별 비중</div>', unsafe_allow_html=True)
        # Assets (Row 2-5, Col P-R)
        asset_df = df.iloc[1:5, 15:18].copy()
        for _, r in asset_df.iterrows():
            if pd.isna(r[15]): continue
            p = parse_numeric(r[17])
            st.write(f"**{r[15]}** <span style='float:right;'>{p}%</span>", unsafe_allow_html=True)
            st.progress(max(0.0, min(p/100.0, 1.0)))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="custom-card"><div class="card-title">증권사별 비중</div>', unsafe_allow_html=True)
        # Brokers (Row 2-15, Col L-M)
        br_df = df.iloc[1:15, 11:13].copy()
        for _, r in br_df.iterrows():
            if pd.isna(r[11]) or r[11] == "비중" or r[11] == "증권사": continue
            p = parse_numeric(r[12])
            st.write(f"**{r[11]}** <span style='float:right;'>{p}%</span>", unsafe_allow_html=True)
            st.progress(max(0.0, min(p/100.0, 1.0)))
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.metric("현금 보유량", f"{int(sm['cash']):,}원")
        st.markdown('</div>', unsafe_allow_html=True)

    st.caption(f"Last Sync: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.error("구글 시트의 '대시보드' 탭을 찾을 수 없거나 접근 권한이 없습니다.")


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
    loss_cnt = parse_val(df.iloc[9, 17])
    invest_start = str(df.iloc[15, 15])
    invest_days = str(df.iloc[15, 17])
    real_total = sm["total"] if sm["total"] > 0 else (sm["eval"] + sm["cash"])

    # UI 렌더링
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; padding:20px 0;">
        <div>
            <div style="color:#64748b; font-size:0.9rem;">총 자산 (Hstock V1.1)</div>
            <div style="font-size:2.8rem; font-weight:800; color:#0f172a;">{int(real_total):,}원</div>
        </div>
        <div style="text-align:right; color:#64748b;">
            <div style="font-size:0.9rem;">투자 정보</div>
            <div style="font-size:1.1rem; font-weight:600; color:#1e293b;">{invest_start} | <span style="color:#6366f1">{invest_days}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("주식 평가금액", f"{int(sm['eval']):,}원")
    m2.metric("매수금액", f"{int(sm['buy']):,}원")
    m3.metric("누적 수익금", f"{int(sm['profit']):,}원", sm['rate'])
    m4.metric("금일 변동액", f"{int(sm['daily']):+,}원")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("총 종목수", f"{len(stocks)}종목")
    win_p = (win_cnt/len(stocks)*100) if len(stocks)>0 else 0
    m6.metric("수익 종목", f"{int(win_cnt)}", f"{win_p:.1f}%")
    loss_p = (loss_cnt/len(stocks)*100) if len(stocks)>0 else 0
    m7.metric("손실 종목", f"{int(loss_cnt)}", f"-{loss_p:.1f}%", delta_color="inverse")
    m8.metric("누적 총수익", f"{int(sm['accum']):,}원")

    st.divider()

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown('<div class="custom-card"><div class="card-title">보유 종목 현황</div>', unsafe_allow_html=True)
        t_df = stocks[['Name', 'Weight', 'CurPrice', 'AvgPrice', 'Rate']].copy()
        t_df.columns = ['종목명', '비중', '현재가', '평단가', '수익률']
        st.dataframe(t_df, hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="custom-card"><div class="card-title">종목별 수익금</div>', unsafe_allow_html=True)
        c_data = stocks[stocks['Profit'] != 0].copy()
        c_data['Profit'] = c_data['Profit'].apply(parse_val)
        st.bar_chart(data=c_data, x='Name', y='Profit', color="#6366f1")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="custom-card"><div class="card-title">자산/증권사 비중</div>', unsafe_allow_html=True)
        # 자산 비중
        asset_df = df.iloc[1:5, 15:18].copy()
        for _, r in asset_df.iterrows():
            if pd.isna(r[15]): continue
            p = parse_val(r[17])
            st.write(f"**{r[15]}** ({p}%)")
            # 에러 방지: 0.0 ~ 1.0 사이로 값 고정
            st.progress(max(0.0, min(p/100.0, 1.0)))
        
        st.divider()
        # 증권사 비중
        br_df = df.iloc[1:15, 11:13].copy()
        for _, r in br_df.iterrows():
            if pd.isna(r[11]) or r[11] == "비중" or r[11] == "증권사": continue
            p = parse_val(r[12])
            st.write(f"**{r[11]}** ({p}%)")
            st.progress(max(0.0, min(p/100.0, 1.0)))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.metric("현금 보유량", f"{int(sm['cash']):,}원")
        st.markdown('</div>', unsafe_allow_html=True)

    st.caption(f"동기화 시간: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.error("데이터 로딩 실패")
