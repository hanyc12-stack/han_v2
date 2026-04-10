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

# 2. 스타일링 (라이트 모드 최적화 및 텍스트 시인성 개선)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
    }

    /* 메트릭 카드 스타일 */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* 텍스트 색상 강제 지정 해제 (테마 호환성) */
    div[data-testid="stMetricValue"] > div {
        font-size: 1.8rem !important;
        font-weight: 700;
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
</style>
""", unsafe_allow_html=True)

# 3. 데이터 파싱 함수 (강화됨)
def parse_val(v):
    if pd.isna(v) or v == "" or v == "-": return 0
    # 숫자, 점, 마이너스 기호만 남기고 모두 제거
    s = str(v).replace(',', '').replace('원', '').replace('%', '').strip()
    try:
        # 공백 제거 후 숫자로 변환
        s = s.replace(" ", "")
        if not s: return 0
        return float(s)
    except:
        # 정규표현식으로 숫자 형태만 추출
        nums = re.findall(r'-?\d+\.?\d*', s)
        return float(nums[0]) if nums else 0

# 4. 데이터 로드
SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=30)
def get_data():
    try:
        resp = requests.get(CSV_URL)
        resp.encoding = 'utf-8'
        return pd.read_csv(io.StringIO(resp.text), header=None)
    except Exception as e:
        st.error(f"시트 데이터를 가져오지 못했습니다: {e}")
        return None

df = get_data()

if df is not None:
    # --- 데이터 행 위치 자동 찾기 ---
    # 종목 데이터 파싱 (1~9행, 12~15행)
    domestic = df.iloc[1:9, 0:10].copy()
    us_stocks = df.iloc[11:15, 0:10].copy()
    stocks = pd.concat([domestic, us_stocks])
    stocks.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    stocks = stocks[stocks['Name'].notna() & (stocks['Name'].str.strip() != "") & (stocks['Name'] != "현금")].copy()
    
    # 총계 행(Row 18) 및 현금 행(Row 17) 찾기
    total_row = df.iloc[17] # 기본값 18행
    cash_row = df.iloc[16]  # 기본값 17행
    
    # 혹시 위치가 바뀌었을 경우를 대비해 검색
    for i in range(len(df)):
        cell_v = str(df.iloc[i, 0]).strip()
        if "Total" in cell_v: total_row = df.iloc[i]
        if "현금" in cell_v and i > 10: cash_row = df.iloc[i]

    # 주요 지표 추출
    summary = {
        "eval_total":  parse_val(total_row[3]), # 주식 평가금액 (D)
        "buy_total":   parse_val(total_row[4]), # 매수금액 (E)
        "profit":      parse_val(total_row[5]), # 누적 수익금 (F)
        "rate":        str(total_row[6]),        # 수익률 (G)
        "daily":       parse_val(total_row[7]), # 금일 변동액 (H)
        "accum_total": parse_val(total_row[8]), # 누적 총수익 (I)
        "cash":        parse_val(cash_row[3]),  # 현금 보유액 (D)
        "total_asset": parse_val(total_row[13]), # 총 자산 (N)
    }
    
    # 통계 (Q10, R10) 및 투자정보 (P16, R16)
    win_cnt = parse_val(df.iloc[9, 16])
    loss_cnt = parse_val(df.iloc[9, 17])
    invest_start = str(df.iloc[15, 15])
    invest_days = str(df.iloc[15, 17])

    # 총자산 계산 보정
    real_total = summary["total_asset"] if summary["total_asset"] > 0 else (summary["eval_total"] + summary["cash"])

    # --- UI 시작 ---
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; padding:20px 0;">
        <div>
            <div style="color:#64748b; font-size:0.9rem; font-weight:500;">총 자산 (Hstock V1.1)</div>
            <div style="font-size:2.8rem; font-weight:800; color:#0f172a;">{int(real_total):,}원</div>
        </div>
        <div style="text-align:right;">
            <div style="color:#64748b; font-size:0.9rem;">투자 정보</div>
            <div style="font-size:1.1rem; font-weight:600;">{invest_start} | <span style="color:#6366f1">{invest_days}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 지표 격자
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("주식 평가금액", f"{int(summary['eval_total']):,}원")
    m2.metric("매수금액", f"{int(summary['buy_total']):,}원")
    m3.metric("누적 수익금", f"{int(summary['profit']):,}원", summary['rate'])
    m4.metric("금일 변동액", f"{int(summary['daily']):+,}원")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("총 종목수", f"{len(stocks)}종목")
    win_pct = (win_cnt / len(stocks) * 100) if len(stocks) > 0 else 0
    m6.metric("수익 종목", f"{int(win_cnt)}", f"{win_pct:.1f}%")
    loss_pct = (loss_cnt / len(stocks) * 100) if len(stocks) > 0 else 0
    m7.metric("손실 종목", f"{int(loss_cnt)}", f"-{loss_pct:.1f}%", delta_color="inverse")
    m8.metric("누적 총수익", f"{int(summary['accum_total']):,}원")

    st.write("---")

    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown('<div class="custom-card"><div class="card-title">보유 종목 현황</div>', unsafe_allow_html=True)
        t_df = stocks[['Name', 'Weight', 'CurPrice', 'AvgPrice', 'Rate']].copy()
        t_df.columns = ['종목명', '비중', '현재가', '평단가', '수익률']
        st.dataframe(t_df, hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="custom-card"><div class="card-title">종목별 수익금</div>', unsafe_allow_html=True)
        chart_data = stocks[stocks['Profit'] != 0].copy()
        chart_data['Profit'] = chart_data['Profit'].apply(parse_val)
        st.bar_chart(data=chart_data, x='Name', y='Profit', color="#6366f1")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="custom-card"><div class="card-title">자산/증권사 비중</div>', unsafe_allow_html=True)
        # 자산 비중 표시
        asset_df = df.iloc[1:5, 15:18].copy()
        for _, r in asset_df.iterrows():
            if pd.isna(r[15]): continue
            p = parse_val(r[17])
            st.write(f"**{r[15]}** ({p}%)")
            st.progress(min(p/100, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.metric("현금 보유량", f"{int(summary['cash']):,}원")
        st.markdown('</div>', unsafe_allow_html=True)

    st.caption(f"최종 업데이트: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.error("데이터를 불러올 수 없습니다.")
