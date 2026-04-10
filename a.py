import streamlit as st
import pandas as pd
import requests
import io
import re

# 1. 페이지 설정
st.set_page_config(
    page_title="Hstock V1.1 Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 데이터 엔진 함수
def parse_numeric(v):
    if pd.isna(v) or v == "" or v == "-": return 0.0
    s = str(v).replace(',', '').replace('원', '').replace('%', '').strip()
    s = s.replace(" ", "")
    try:
        return float(s)
    except:
        nums = re.findall(r'-?\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0

def format_price(v):
    try:
        val = parse_numeric(v)
        if val == 0 and (pd.isna(v) or str(v).strip() in ["-", ""]):
            return "-"
        return f"{int(val):,}"
    except:
        return "-"

# 대시보드 시트 GID (1550923272)
SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg"
GID = "1550923272" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&range=A:Z&gid={GID}"

@st.cache_data(ttl=10)
def fetch_data():
    try:
        resp = requests.get(CSV_URL)
        resp.encoding = 'utf-8'
        raw_df = pd.read_csv(io.StringIO(resp.text), header=None)
        # 최소 25개 컬럼 보장
        return raw_df.reindex(columns=range(max(25, raw_df.shape[1])))
    except:
        return None

df = fetch_data()

if df is not None:
    # --- 데이터 추출 및 정밀 매핑 ---
    # 사용자 확인 기반 매핑 (A:0, B:1, C:2, D:3, E:4, F:5, G:6, H:7, I:8, J:9)
    # 현재가:J(9), 평단가:I(8), 주당전일비:F(5), 금액 전일비:G(6), 수익금:H(7), 수익률:L(11), 비중:B(1)
    # 컬럼 인덱스: 0:Name, 1:Weight, 2:Qty, 3:CurAmt, 4:BuyAmt, 7:Profit(H), 8:AvgPrice(I), 9:CurPrice(J), 5:Diff(F), 6:TotalDiff(G), 11:Rate(L)
    cols = [0, 1, 2, 3, 4, 7, 8, 9, 5, 6, 11]
    
    # 동적 행 추출: 고정 범위를 넓히고 불필요한 행(헤더 등) 필터링
    exclude_keywords = ["비중", "유형", "항목", "증권사", "Total", "합계", "계", "total", "합", "종목", "Name"]
    
    raw_stocks = df.iloc[1:60, cols].copy()
    raw_stocks.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'TotalDiff', 'Rate']
    
    stocks = raw_stocks[
        raw_stocks['Name'].notna() & 
        (raw_stocks['Name'].str.strip() != "") & 
        (~raw_stocks['Name'].str.contains('|'.join(exclude_keywords), case=False)) &
        (raw_stocks['Weight'].str.strip() != "비중")
    ].drop_duplicates(subset=['Name']).copy()

    row_total = df.iloc[17]
    row_sub = df.iloc[16]
    
    invest_start = str(df.iloc[11, 15])           # P12: 투자 시작일
    invest_days = str(df.iloc[11, 17])            # R12: 투자일/경과일
    
    total_asset_q6 = parse_numeric(df.iloc[5, 16]) # Q6: 전체 자산 합계

    sm = {
        "eval":   parse_numeric(row_total[21]),    # V (인덱스 21)
        "buy":    parse_numeric(row_total[22]),    # W (인덱스 22)
        "profit": parse_numeric(row_total[23]),    # X (인덱스 23)
        "rate":   str(row_total[24]),              # Y (인덱스 24) - 수익률
        "daily":  parse_numeric(row_total[9]),     # J18 (인덱스 9)
        "accum":  parse_numeric(row_total[8]),
        "cash":   parse_numeric(row_sub[3]),
        "total":  total_asset_q6 if total_asset_q6 > 0 else parse_numeric(row_total[13]),
    }
    real_total = sm["total"] if sm["total"] > 0 else (sm["eval"] + sm["cash"])

    def get_color_class(val):
        nums = parse_numeric(val)
        return 'up' if nums > 0 else 'down' if nums < 0 else 'flat'

    # --- UI 템플릿 및 스타일 ---
    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Noto Sans KR', sans-serif;
            background: #f5f5f3; color: #1a1a18;
        }}
        @media (prefers-color-scheme: dark) {{
            [data-testid="stAppViewContainer"] {{ background: #1a1a18; color: #e8e6df; }}
            .card {{ background: #242422 !important; border-color: rgba(255,255,255,0.1) !important; }}
            .metric-card {{ background: #2c2c2a !important; }}
            .stock-table th {{ color: #888780 !important; border-color: rgba(255,255,255,0.1) !important; }}
            .stock-table td {{ border-color: rgba(255,255,255,0.07) !important; color: #e8e6df !important; }}
            .card-title, .metric-label, .metric-sub {{ color: #888780 !important; }}
        }}
        .dash {{ max-width: 1300px; margin: 0 auto; padding: 12px 24px; }}
        .header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 28px; }}
        .header-left .total {{ font-size: 34px; font-weight: 700; letter-spacing: -0.8px; color: #1a1a18; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px; margin-bottom: 28px; }}
        .metric-card {{ background: #fff; border: 1px solid rgba(0,0,0,0.05); border-radius: 16px; padding: 22px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); }}
        .metric-label {{ font-size: 13.5px; color: #888780; margin-bottom: 10px; font-weight: 500; }}
        .metric-value {{ font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
        .metric-sub {{ font-size: 14px; margin-top: 6px; font-weight: 500; }}
        .up {{ color: #D85A30 !important; }}
        .down {{ color: #3266AD !important; }}
        .flat {{ color: #888780 !important; }}
        .card {{ background: #fff; border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 32px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); }}
        .card-title {{ font-size: 18px; font-weight: 700; color: #1a1a18; margin-bottom: 28px; display: flex; align-items: center; gap: 10px; }}
        .stock-table {{ width: 100%; border-collapse: collapse; font-size: 14.5px; }}
        .stock-table th {{ color: #888780; font-weight: 600; padding: 14px 10px; text-align: right; border-bottom: 1.5px solid rgba(0,0,0,0.08); font-size: 13.5px; }}
        .stock-table th:first-child {{ text-align: left; width: 180px; }}
        .stock-table td {{ padding: 18px 10px; text-align: right; border-bottom: 1px solid rgba(0,0,0,0.04); }}
        .stock-table td:first-child {{ text-align: left; font-weight: 700; color: #1a1a18; font-size: 15px; }}
        .badge {{ display: inline-block; font-size: 12px; padding: 4px 12px; border-radius: 6px; font-weight: 700; }}
        .badge.up {{ background: #FAECE7; color: #D85A30; }}
        .badge.down {{ background: #E7F0FA; color: #3266AD; }}
        .badge.flat {{ background: #F0F0F0; color: #888780; }}
        
        /* 컬럼 너비 클래스 */
        .col-name {{ width: 180px; }}
        .col-weight {{ width: 80px; }}
        .col-price {{ width: 130px; }}
        .col-change {{ width: 140px; }}
        .col-profit {{ width: 180px; }}

        @media (max-width: 1024px) {{
          .metric-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
          .stock-table {{ font-size: 13.5px; }}
        }}
        @media (max-width: 768px) {{
          .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
          .stock-table {{ font-size: 12.5px; }}
          .header {{ flex-direction: column; gap: 14px; align-items: flex-start; }}
          .header-right {{ text-align: left !important; }}
        }}
    </style>
    
    <div class="dash">
      <div class="header">
        <div class="header-left">
          <div class="sub" style="font-size:14px; color:#888780; margin-bottom:6px;">총 자산 (Hstock V1.1)</div>
          <div class="total">{int(real_total):,}원</div>
        </div>
        <div class="header-right" style="text-align:right;">
          <div class="sub" style="font-size:14px; color:#888780; margin-bottom:6px;">투자 시작일</div>
          <div class="date" style="font-size:17px; font-weight:600;">{invest_start} <span style="color:#888780; font-weight:400; margin-left:8px;">| {invest_days}</span></div>
        </div>
      </div>

      <div class="metric-grid">
        <div class="metric-card"><div class="metric-label">주식 평가금액</div><div class="metric-value">{int(sm['eval']):,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card"><div class="metric-label">매수금액</div><div class="metric-value">{int(sm['buy']):,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card">
          <div class="metric-label">누적 수익금</div>
          <div class="metric-value {get_color_class(sm['profit'])}">
            {int(sm['profit']):+,}
            <span style="font-size:15px; font-weight:500; margin-left:4px;">({sm['rate']})</span>
          </div>
          <div class="metric-sub">원</div>
        </div>
        <div class="metric-card"><div class="metric-label">금일 변동액</div><div class="metric-value {get_color_class(sm['daily'])}">{int(sm['daily']):+,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card"><div class="metric-label">현금 보유량</div><div class="metric-value">{int(sm['cash']):,}</div><div class="metric-sub">원</div></div>
      </div>

      <div class="card" style="width: 100%;">
        <div class="card-title">📦 보유 종목 현황</div>
        <table class="stock-table">
          <thead>
            <tr>
              <th class="col-name">종목명</th>
              <th class="col-weight">비중</th>
              <th class="col-price">현재가</th>
              <th class="col-price">평단가</th>
              <th class="col-change">주당전일비</th>
              <th class="col-change">금액 전일비</th>
              <th class="col-profit">수익금(수익률)</th>
            </tr>
          </thead>
          <tbody>
            {''.join([
                f"""<tr>
                    <td>{r['Name']}</td>
                    <td>{r['Weight']}</td>
                    <td>{format_price(r['CurPrice'])}</td>
                    <td>{format_price(r['AvgPrice'])}</td>
                    <td class='{get_color_class(r['Diff'])}'>{format_price(r['Diff'])}</td>
                    <td class='{get_color_class(r['TotalDiff'])}'>
                        {format_price(r['TotalDiff'])}
                    </td>
                    <td><span class='badge {get_color_class(r['Profit'])}'>
                        {format_price(r['Profit'])} ({r['Rate']})
                    </span></td>
                </tr>""" for _, r in stocks.iterrows()
            ])}
          </tbody>
        </table>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.error("데이터 로딩 실패")
