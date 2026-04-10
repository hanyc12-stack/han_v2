`ValueError` 문제는 종목 리스트의 **'현금'** 항목처럼 현재가가 숫자가 아닌 경우(예: `-`) 발생합니다. 이를 안전하게 처리할 수 있도록 숫자인 경우만 콤마(,)를 붙이고, 그 외에는 그대로 표시하도록 수정했습니다.

아래 코드를 전체 복사하여 **`a.py`**에 덮어쓰기 해주시면 에러 없이 정상적으로 작동합니다.

```python
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
    # 숫자로 변환 가능한 경우만 콤마 포맷팅, 아니면 그대로 반환
    try:
        val = parse_numeric(v)
        if val == 0 and (pd.isna(v) or str(v).strip() in ["-", ""]):
            return "-"
        return f"{int(val):,}"
    except:
        return "-"

# 시트 설정 (GID 1550923272)
SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg"
GID = "1550923272" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=15)
def fetch_data():
    try:
        resp = requests.get(CSV_URL)
        resp.encoding = 'utf-8'
        return pd.read_csv(io.StringIO(resp.text), header=None)
    except:
        return None

df = fetch_data()

if df is not None:
    # --- 데이터 추출 ---
    dom = df.iloc[1:9, 0:10].copy()
    us = df.iloc[11:15, 0:10].copy()
    stocks_raw = pd.concat([dom, us])
    stocks_raw.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    stocks = stocks_raw[stocks_raw['Name'].notna() & (stocks_raw['Name'].str.strip() != "")].copy()

    # 요약 지표
    row_total = df.iloc[17]
    row_sub = df.iloc[16]
    
    total_cnt = parse_numeric(df.iloc[7, 15]) 
    win_cnt = parse_numeric(df.iloc[7, 16])   
    loss_cnt = parse_numeric(df.iloc[7, 17])  
    invest_start = str(df.iloc[10, 16])       
    invest_days = str(df.iloc[10, 17])        

    win_p = (win_cnt / total_cnt * 100) if total_cnt > 0 else 0.0
    loss_p = (loss_cnt / total_cnt * 100) if total_cnt > 0 else 0.0

    sm = {
        "eval":  parse_numeric(row_total[3]),
        "buy":   parse_numeric(row_total[4]),
        "profit": parse_numeric(row_total[5]),
        "rate":  str(row_total[6]),
        "daily": parse_numeric(row_total[7]),
        "accum": parse_numeric(row_total[8]),
        "cash":  parse_numeric(row_sub[3]),
        "total": parse_numeric(row_total[13]),
    }
    
    real_total = sm["total"] if sm["total"] > 0 else (sm["eval"] + sm["cash"])

    # 3. HTML/CSS 템플릿
    st.markdown(f"""
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
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
        .header-left .total {{ font-size: 30px; font-weight: 500; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 16px; }}
        .metric-card {{ background: #ebebea; border-radius: 8px; padding: 14px 16px; }}
        .metric-label {{ font-size: 12px; color: #888780; margin-bottom: 4px; }}
        .metric-value {{ font-size: 20px; font-weight: 500; }}
        .metric-sub {{ font-size: 12px; margin-top: 3px; color: #888780; }}
        .up {{ color: #1D9E75 !important; }}
        .down {{ color: #D85A30 !important; }}
        .grid2 {{ display: grid; grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr); gap: 16px; margin-bottom: 16px; }}
        .card {{ background: #fff; border: 0.5px solid rgba(0,0,0,0.12); border-radius: 12px; padding: 16px; }}
        .card-title {{ font-size: 13px; font-weight: 500; color: #888780; margin-bottom: 14px; }}
        .stock-table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
        .stock-table th {{ color: #888780; font-weight: 500; padding: 4px 6px 8px; text-align: right; border-bottom: 0.5px solid rgba(0,0,0,0.1); }}
        .stock-table th:first-child {{ text-align: left; }}
        .stock-table td {{ padding: 7px 6px; text-align: right; border-bottom: 0.5px solid rgba(0,0,0,0.06); }}
        .stock-table td:first-child {{ text-align: left; font-weight: 500; }}
        .badge {{ display: inline-block; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 500; }}
        .badge.up {{ background: #EAF3DE; color: #3B6D11; }}
        .badge.down {{ background: #FAECE7; color: #993C1D; }}
        .badge.flat {{ background: #ebebea; color: #888780; }}
        .bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 9px; font-size: 12px; }}
        .bar-label {{ width: 90px; color: #888780; flex-shrink: 0; }}
        .bar-track {{ flex: 1; height: 7px; background: #ebebea; border-radius: 4px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 4px; }}
        .bar-pct {{ width: 38px; text-align: right; font-weight: 500; }}
        @media (max-width: 700px) {{
          .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
          .grid2 {{ grid-template-columns: 1fr; }}
          .header {{ flex-direction: column; gap: 8px; }}
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
          <div class="date" style="font-size:14px; font-weight:500;">{invest_start} <span style="color:#888780; font-weight:400;">| {invest_days}</span></div>
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

      <div class="metric-grid">
        <div class="metric-card"><div class="metric-label">총 종목수</div><div class="metric-value">{int(total_cnt)}</div><div class="metric-sub">종목</div></div>
        <div class="metric-card">
          <div class="metric-label">수익 종목</div>
          <div class="metric-value up">{int(win_cnt)}</div>
          <div class="metric-sub up">{win_p:.1f}%</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">손실 종목</div>
          <div class="metric-value down">{int(loss_cnt)}</div>
          <div class="metric-sub down">{loss_p:.1f}%</div>
        </div>
        <div class="metric-card"><div class="metric-label">누적 총수익</div><div class="metric-value" style="font-size:17px;">{int(sm['accum']):,}</div><div class="metric-sub">원</div></div>
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

        <div style="display:flex;flex-direction:column;gap:16px;">
          <div class="card">
            <div class="card-title">자산 유형별 비중</div>
            {''.join([f"<div class='bar-row'><div class='bar-label'>{r[15]}</div><div class='bar-track'><div class='bar-fill' style='width:{parse_numeric(r[17])}%;background:{'#3266AD' if r[15]=='국내주식' else '#1D9E75' if r[15]=='안전자산' else '#7F77DD' if r[15]=='해외성장' else '#D85A30'};'></div></div><div class='bar-pct'>{r[17]}</div></div>" for _, r in df.iloc[1:5, 15:18].iterrows() if not pd.isna(r[15])])}
          </div>
          <div class="card" style="padding: 12px 16px;">
            <div class="metric-label">현금 보유량</div>
            <div class="metric-value">{int(sm['cash']):,}원</div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:0;">
        <div class="card-title">종목별 수익금 비교</div>
        <div style="width:100%;height:220px;"><canvas id="pChart"></canvas></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 차트 스크립트
    c_stocks = stocks[stocks['Profit'] != 0].copy()
    c_stocks['Profit'] = c_stocks['Profit'].apply(parse_numeric)
    c_stocks = c_stocks.sort_values('Profit', ascending=False)
    
    st.components.v1.html(f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <div style="height: 220px;"><canvas id="ctx"></canvas></div>
    <script>
      new Chart(document.getElementById('ctx'), {{
        type: 'bar',
        data: {{
          labels: {c_stocks['Name'].tolist()},
          datasets: [{{
            data: {c_stocks['Profit'].tolist()},
            backgroundColor: {['#1D9E75' if v >= 0 else '#D85A30' for v in c_stocks['Profit'].tolist()]},
            borderRadius: 3,
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: true }} }},
          scales: {{
            x: {{ ticks: {{ font: {{ size: 11 }}, color: '#888780' }}, grid: {{ display: false }} }},
            y: {{ ticks: {{ color: '#888780' }}, grid: {{ color: 'rgba(136,135,128,0.1)' }} }}
          }}
        }}
      }});
    </script>
    """, height=240)
else:
    st.error("데이터 로딩 실패")
```
