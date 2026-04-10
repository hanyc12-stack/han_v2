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
        return pd.read_csv(io.StringIO(resp.text), header=None)
    except:
        return None

df = fetch_data()

if df is not None:
    # --- 데이터 추출 및 정밀 매핑 ---
    # 사용 컬럼: 0:명칭, 1:비중, 2:수량, 3:평가금, 4:매수금, 5:수익금, 6:평단가, 7:현재가, 20:전일비(U), 9:수익률(J)
    cols = [0, 1, 2, 3, 4, 5, 6, 7, 20, 9]
    dom = df.iloc[1:9, cols].copy()
    us = df.iloc[11:15, cols].copy()
    stocks_raw = pd.concat([dom, us])
    stocks_raw.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    # stocks 전처리: Name이 있고 공백이 아닌 것만
    stocks = stocks_raw[stocks_raw['Name'].notna() & (stocks_raw['Name'].str.strip() != "")].copy()

    row_total = df.iloc[17]
    row_sub = df.iloc[16]
    
    invest_start = str(df.iloc[11, 15])           # P12: 투자 시작일
    invest_days = str(df.iloc[11, 17])            # R12: 투자일/경과일
    
    total_asset_q6 = parse_numeric(df.iloc[5, 16]) # Q6: 전체 자산 합계

    sm = {
        "eval":  parse_numeric(row_total[3]),
        "buy":   parse_numeric(row_total[4]),
        "profit": parse_numeric(row_total[5]),
        "rate":  str(row_total[6]),
        "daily": parse_numeric(row_total[7]),
        "accum": parse_numeric(row_total[8]),
        "cash":  parse_numeric(row_sub[3]),
        "total": total_asset_q6 if total_asset_q6 > 0 else parse_numeric(row_total[13]),
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
        .dash {{ max-width: 1250px; margin: 0 auto; padding: 12px 24px; }}
        .header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 24px; }}
        .header-left .total {{ font-size: 32px; font-weight: 700; letter-spacing: -0.5px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 24px; }}
        .metric-card {{ background: #ebebea; border-radius: 12px; padding: 16px; transition: all 0.2s; }}
        .metric-label {{ font-size: 11px; color: #888780; margin-bottom: 6px; font-weight: 500; }}
        .metric-value {{ font-size: 20px; font-weight: 700; }}
        .metric-sub {{ font-size: 13px; margin-top: 4px; font-weight: 500; }}
        .up {{ color: #D85A30 !important; }}
        .down {{ color: #3266AD !important; }}
        .flat {{ color: #888780 !important; }}
        .card {{ background: #fff; border: 1px solid rgba(0,0,0,0.08); border-radius: 18px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01); }}
        .card-title {{ font-size: 15px; font-weight: 700; color: #333; margin-bottom: 20px; }}
        .stock-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .stock-table th {{ color: #888780; font-weight: 500; padding: 8px 6px; text-align: right; border-bottom: 1px solid rgba(0,0,0,0.08); }}
        .stock-table th:first-child {{ text-align: left; }}
        .stock-table td {{ padding: 12px 6px; text-align: right; border-bottom: 1px solid rgba(0,0,0,0.04); }}
        .stock-table td:first-child {{ text-align: left; font-weight: 600; color: #1a1a18; }}
        .badge {{ display: inline-block; font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; }}
        .badge.up {{ background: #FAECE7; color: #D85A30; }}
        .badge.down {{ background: #E7F0FA; color: #3266AD; }}
        .badge.flat {{ background: #F0F0F0; color: #888780; }}
        @media (max-width: 1024px) {{
          .metric-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
          .stock-table {{ font-size: 12px; }}
        }}
        @media (max-width: 768px) {{
          .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
          .stock-table {{ font-size: 11px; }}
        }}
    </style>
    
    <div class="dash">
      <div class="header">
        <div class="header-left">
          <div class="sub" style="font-size:12px; color:#888780;">총 자산 (Hstock V1.1)</div>
          <div class="total">{int(real_total):,}원</div>
        </div>
        <div class="header-right" style="text-align:right;">
          <div class="sub" style="font-size:12px; color:#888780;">투자 시작일</div>
          <div class="date" style="font-size:15px; font-weight:600;">{invest_start} <span style="color:#888780; font-weight:400; margin-left:4px;">| {invest_days}</span></div>
        </div>
      </div>

      <div class="metric-grid">
        <div class="metric-card"><div class="metric-label">주식 평가금액</div><div class="metric-value">{int(sm['eval']):,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card"><div class="metric-label">매수금액</div><div class="metric-value">{int(sm['buy']):,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card">
          <div class="metric-label">누적 수익금</div>
          <div class="metric-value {get_color_class(sm['profit'])}">{int(sm['profit']):+,}</div>
          <div class="metric-sub {get_color_class(sm['profit'])}">{sm['rate']}</div>
        </div>
        <div class="metric-card"><div class="metric-label">금일 변동액</div><div class="metric-value {get_color_class(sm['daily'])}">{int(sm['daily']):+,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card"><div class="metric-label">현금 보유량</div><div class="metric-value">{int(sm['cash']):,}</div><div class="metric-sub">원</div></div>
      </div>

      <div class="card" style="width: 100%;">
        <div class="card-title">보유 종목 현황</div>
        <table class="stock-table">
          <thead>
            <tr>
              <th>종목명</th>
              <th>비중</th>
              <th>현재가</th>
              <th>평단가</th>
              <th>주당 전일비</th>
              <th>일일 총변동</th>
              <th>수익금(수익률)</th>
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
                    <td class='{get_color_class(parse_numeric(r['Qty']) * parse_numeric(r['Diff']))}'>
                        {format_price(parse_numeric(r['Qty']) * parse_numeric(r['Diff']))}
                    </td>
                    <td><span class='badge {get_color_class(r['Profit'])}'>
                        {format_price(r['Profit'])} ({r['Rate']})
                    </span></td>
                </tr>""" for _, r in stocks.iterrows() if r['Name'].strip() not in ["", "합계"]
            ])}
          </tbody>
        </table>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.error("데이터 로딩 실패")
