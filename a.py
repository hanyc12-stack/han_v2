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
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

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
    dom = df.iloc[1:9, 0:10].copy()
    us = df.iloc[11:15, 0:10].copy()
    stocks_raw = pd.concat([dom, us])
    stocks_raw.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    # stocks 전처리: Name이 있고 공백이 아닌 것만
    stocks = stocks_raw[stocks_raw['Name'].notna() & (stocks_raw['Name'].str.strip() != "")].copy()

    row_total = df.iloc[17]
    row_sub = df.iloc[16]
    
    total_cnt = parse_numeric(df.iloc[8, 15])     # P9: 종목수
    win_cnt = parse_numeric(df.iloc[8, 16])       # Q9: 수익 종목수
    win_p_str = str(df.iloc[9, 16])               # Q10: 수익률%
    loss_cnt = parse_numeric(df.iloc[8, 17])      # R9: 손실 종목수
    loss_p_str = str(df.iloc[9, 17])              # R10: 손실률%
    
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
        "total":    # --- UI 템플릿 ---
    # 색상 팔레트 정의 (이미지 참고)
    brokerage_colors = ['#3266AD', '#7F77DD', '#1D9E75', '#EAB308', '#D85A30', '#DB2777', '#888780', '#6366F1', '#10B981', '#F59E0B']
    
    # 제외 키워드 리스트 (헤더/합계 행 필터링)
    exclude_list = ["비중", "유형", "항목", "증권사", "Total", "합계", "계", "total", "합", "종목"]

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f3; color: #1a1a18;
        }}
        @media (prefers-color-scheme: dark) {{
            [data-testid="stAppViewContainer"] {{ background: #1a1a18; color: #e8e6df; }}
            .card {{ background: #242422 !important; border-color: rgba(255,255,255,0.1) !important; }}
            .metric-card {{ background: #2c2c2a !important; }}
            .stock-table th {{ color: #888780 !important; border-color: rgba(255,255,255,0.1) !important; }}
            .stock-table td {{ border-color: rgba(255,255,255,0.07) !important; color: #e8e6df !important; }}
            .bar-track {{ background: #3a3a38 !important; }}
            .card-title, .metric-label, .metric-sub, .bar-label {{ color: #888780 !important; }}
        }}
        .dash {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
        .header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }}
        .header-left .total {{ font-size: 32px; font-weight: 700; letter-spacing: -0.5px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 20px; }}
        .metric-card {{ background: #ebebea; border-radius: 12px; padding: 16px; transition: all 0.2s; }}
        .metric-label {{ font-size: 12px; color: #888780; margin-bottom: 6px; font-weight: 500; }}
        .metric-value {{ font-size: 22px; font-weight: 700; }}
        .metric-sub {{ font-size: 13px; margin-top: 4px; font-weight: 500; }}
        .up {{ color: #1D9E75 !important; }}
        .down {{ color: #D85A30 !important; }}
        .grid2 {{ display: grid; grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: #fff; border: 1px solid rgba(0,0,0,0.08); border-radius: 18px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01); }}
        .card-title {{ font-size: 15px; font-weight: 700; color: #333; margin-bottom: 24px; }}
        .stock-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
        .stock-table th {{ color: #888780; font-weight: 500; padding: 8px 6px; text-align: right; border-bottom: 1px solid rgba(0,0,0,0.08); }}
        .stock-table th:first-child {{ text-align: left; }}
        .stock-table td {{ padding: 12px 6px; text-align: right; border-bottom: 1px solid rgba(0,0,0,0.04); }}
        .stock-table td:first-child {{ text-align: left; font-weight: 600; color: #1a1a18; }}
        .badge {{ display: inline-block; font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; }}
        .badge.up {{ background: #EAF3DE; color: #3B6D11; }}
        .badge.down {{ background: #FAECE7; color: #993C1D; }}
        .bar-row {{ display: flex; align-items: center; gap: 16px; margin-bottom: 18px; font-size: 14px; position: relative; }}
        .bar-label {{ width: 110px; color: #666; flex-shrink: 0; font-weight: 500; font-size: 14px; }}
        .bar-track {{ flex: 1; height: 10px; background: #f0f0f0; border-radius: 10px; overflow: visible; position: relative; }}
        .bar-fill {{ height: 100%; border-radius: 10px; position: relative; transition: width 0.8s ease; }}
        /* 바 끝에 점 효과 */
        .bar-fill::after {{
            content: ''; position: absolute; right: -2px; top: -1px; width: 12px; height: 12px; 
            border-radius: 50%; background: inherit; border: 2px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .bar-pct {{ width: 60px; text-align: right; font-weight: 700; color: #1a1a18; font-size: 14px; }}
        @media (max-width: 768px) {{
          .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
          .grid2 {{ grid-template-columns: 1fr; }}
          .header {{ flex-direction: column; gap: 12px; }}
          .bar-label {{ width: 90px; font-size: 12px; }}
          .bar-pct {{ width: 50px; font-size: 12px; }}
        }}
    </style>
    
    <div class="dash">
      <div class="header">
        <div class="header-left">
          <div class="sub" style="font-size:12px; color:#888780; margin-bottom:2px;">총 자산 (Hstock V1.1)</div>
          <div class="total">{int(real_total):,}원</div>
        </div>
        <div class="header-right" style="text-align:right;">
          <div class="sub" style="font-size:12px; color:#888780; margin-bottom:2px;">투자 시작일</div>
          <div class="date" style="font-size:15px; font-weight:600;">{invest_start} <span style="color:#888780; font-weight:400; margin-left:4px;">| {invest_days}</span></div>
        </div>
      </div>

      <div class="metric-grid">
        <div class="metric-card"><div class="metric-label">주식 평가금액</div><div class="metric-value">{int(sm['eval']):,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card"><div class="metric-label">매수금액</div><div class="metric-value">{int(sm['buy']):,}</div><div class="metric-sub">원</div></div>
        <div class="metric-card">
          <div class="metric-label">누적 수익금</div>
          <div class="metric-value {'up' if sm['profit']>=0 else 'down'}">{int(sm['profit']):+,}</div>
          <div class="metric-sub {'up' if sm['profit']>=0 else 'down'}">{sm['rate']}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">금일 변동액</div>
          <div class="metric-value {'up' if sm['daily']>=0 else 'down'}">{int(sm['daily']):+,}</div>
          <div class="metric-sub">원</div>
        </div>
      </div>

      <div class="grid2">
        <div class="card">
          <div class="card-title">보유 종목 현황</div>
          <table class="stock-table">
            <thead><tr><th>종목명</th><th>비중</th><th>현재가</th><th>평단가</th><th>수익률</th></tr></thead>
            <tbody>
              {''.join([f"<tr><td>{r['Name']}</td><td>{r['Weight']}</td><td>{format_price(r['CurPrice'])}</td><td>{format_price(r['AvgPrice'])}</td><td><span class='badge {'up' if parse_numeric(r['Rate'])>=0 else 'down' if parse_numeric(r['Rate'])<0 else 'flat'}'>{r['Rate'] if r['Name']!='현금' else '안전자산'}</span></td></tr>" for _, r in stocks.iterrows()])}
            </tbody>
          </table>
        </div>

        <div style="display:flex;flex-direction:column;gap:20px;">
          <div class="card">
            <div class="card-title">자산 유형별 비중</div>
            {''.join([f"<div class='bar-row'><div class='bar-label'>{r[15]}</div><div class='bar-track'><div class='bar-fill' style='width:{parse_numeric(r[17])}%;background:{'#3266AD' if r[15]=='국내주식' else '#1D9E75' if r[15]=='안전자산' else '#7F77DD' if r[15]=='해외성장' else '#D85A30'};'></div></div><div class='bar-pct'>{r[17]}</div></div>" for _, r in df.iloc[0:10, 15:18].iterrows() if not pd.isna(r[15]) and r[15] not in exclude_list and parse_numeric(r[17]) <= 100])}
          </div>
          <div class="card">
            <div class="card-title">증권사별 비중</div>
            {''.join([f"<div class='bar-row'><div class='bar-label'>{r[11]}</div><div class='bar-track'><div class='bar-fill' style='width:{parse_numeric(r[12])}%;background:{brokerage_colors[i % len(brokerage_colors)]};'></div></div><div class='bar-pct'>{r[12]}</div></div>" for i, r in df.iloc[0:20, [11, 12]].iterrows() if not pd.isna(r[11]) and r[11] not in exclude_list and parse_numeric(r[12]) <= 100])}
          </div>
          <div class="card" style="padding: 16px 24px;">
            <div class="metric-label">현금 보유량</div>
            <div class="metric-value" style="font-size:20px; font-weight:700;">{int(sm['cash']):,}원</div>
          </div>
        </div>
      </div>
" for i, r in df.iloc[0:18, [11, 13]].iterrows() if not pd.isna(r[11]) and r[11] not in ["비중", "증권사", "항목"]])}
          </div>
          <div class="card" style="padding: 16px 24px;">
            <div class="metric-label">현금 보유량</div>
            <div class="metric-value" style="font-size:20px; font-weight:700;">{int(sm['cash']):,}원</div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:0; padding-bottom:12px;">
        <div class="card-title">종목별 수익금 비교</div>
        <div id="chart-container" style="width:100%; height:240px;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 차트 엔진 (Chart.js) ---
    c_stocks = stocks[stocks['Profit'] != 0].copy()
    c_stocks['Profit'] = c_stocks['Profit'].apply(parse_numeric)
    c_stocks = c_stocks.sort_values('Profit', ascending=False)
    
    st.components.v1.html(f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <div style="height: 230px;"><canvas id="ctx"></canvas></div>
    <script>
      const ctx = document.getElementById('ctx');
      new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: {c_stocks['Name'].tolist()},
          datasets: [{{
            data: {c_stocks['Profit'].tolist()},
            backgroundColor: {['#3266AD' if v >= 0 else '#D85A30' for v in c_stocks['Profit'].tolist()]},
            borderRadius: 6,
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: true }} }},
          scales: {{
            x: {{ ticks: {{ font: {{ size: 11 }}, color: '#888780' }}, grid: {{ display: false }} }},
            y: {{ ticks: {{ font: {{ size: 10 }}, color: '#888780' }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }}
          }}
        }}
      }});
    </script>
    """, height=240)
else:
    st.error("데이터 로딩 실패")
