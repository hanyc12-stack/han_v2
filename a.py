import streamlit as st
import pandas as pd
import requests
import io
import re

# 1. Page Configuration
st.set_page_config(
    page_title="Hstock V1.1 Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Data Engine Functions
def parse_numeric(v):
    if pd.isna(v) or v == "" or v == "-": return 0.0
    s = str(v).replace(',', '').replace('원', '').replace('%', '').strip()
    s = s.replace(" ", "")
    try:
        return float(s)
    except:
        nums = re.findall(r'-?\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0

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
    # --- Data Extraction ---
    # 1. Stocks
    dom = df.iloc[1:9, 0:10].copy()
    us = df.iloc[11:15, 0:10].copy()
    stocks_raw = pd.concat([dom, us])
    stocks_raw.columns = ['Name', 'Weight', 'Qty', 'CurAmt', 'BuyAmt', 'Profit', 'AvgPrice', 'CurPrice', 'Diff', 'Rate']
    stocks = stocks_raw[stocks_raw['Name'].notna() & (stocks_raw['Name'].str.strip() != "")].copy()

    # 2. Metrics & Stats
    row_total = df.iloc[17]   # 18행
    row_sub = df.iloc[16]     # 17행
    
    total_cnt = parse_numeric(df.iloc[7, 15]) # P8
    win_cnt = parse_numeric(df.iloc[7, 16])   # Q8
    loss_cnt = parse_numeric(df.iloc[7, 17])  # R8
    invest_start = str(df.iloc[10, 16])       # Q11
    invest_days = str(df.iloc[10, 17])        # R11

    sm = {
        "eval":  parse_numeric(row_total[3]),  # D18
        "buy":   parse_numeric(row_total[4]),  # E18
        "profit": parse_numeric(row_total[5]), # F18
        "rate":  str(row_total[6]),            # G18
        "daily": parse_numeric(row_total[7]),  # H18
        "accum": parse_numeric(row_total[8]),  # I18
        "cash":  parse_numeric(row_sub[3]),    # D17
        "total": parse_numeric(row_total[13]), # N18
    }
    
    real_total = sm["total"] if sm["total"] > 0 else (sm["eval"] + sm["cash"])

    # 3. Custom Template Integration (HTML & CSS)
    # Replicating the provided HTML/CSS design exactly.
    st.markdown(f"""
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
            background: #f5f5f3;
            color: #1a1a18;
        }}
        
        @media (prefers-color-scheme: dark) {{
            [data-testid="stAppViewContainer"] {{ background: #1a1a18; color: #e8e6df; }}
            .card {{ background: #242422 !important; border-color: rgba(255,255,255,0.1) !important; }}
            .metric-card {{ background: #2c2c2a !important; }}
            .stock-table th {{ color: #888780 !important; border-color: rgba(255,255,255,0.1) !important; }}
            .stock-table td {{ border-color: rgba(255,255,255,0.07) !important; color: #e8e6df !important; }}
            .badge.flat {{ background: #3a3a38 !important; color: #888780 !important; }}
            .bar-track {{ background: #3a3a38 !important; }}
            .section-title, .card-title, .metric-label, .metric-sub, .bar-label, .legend-item, .invest-info span {{ color: #888780 !important; }}
        }}

        .dash {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}

        /* Header */
        .header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }}
        .header-left .sub {{ font-size: 12px; color: #888780; margin-bottom: 4px; }}
        .header-left .total {{ font-size: 30px; font-weight: 500; color: inherit; }}
        .header-right {{ text-align: right; }}
        .header-right .sub {{ font-size: 12px; color: #888780; margin-bottom: 3px; }}
        .header-right .date {{ font-size: 14px; font-weight: 500; }}
        .header-right .days {{ color: #888780; font-weight: 400; }}

        /* Metric grid */
        .metric-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 16px; }}
        .metric-card {{ background: #ebebea; border-radius: 8px; padding: 14px 16px; }}
        .metric-label {{ font-size: 12px; color: #888780; margin-bottom: 4px; }}
        .metric-value {{ font-size: 20px; font-weight: 500; color: inherit; }}
        .metric-sub {{ font-size: 12px; margin-top: 3px; color: #888780; }}
        .up {{ color: #1D9E75 !important; }}
        .down {{ color: #D85A30 !important; }}

        /* Cards */
        .grid2 {{ display: grid; grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr); gap: 16px; margin-bottom: 16px; }}
        .card {{ background: #fff; border: 0.5px solid rgba(0,0,0,0.12); border-radius: 12px; padding: 16px; }}
        .card-title {{ font-size: 13px; font-weight: 500; color: #888780; margin-bottom: 14px; }}

        /* Table */
        .stock-table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
        .stock-table th {{
          color: #888780; font-weight: 500; padding: 4px 6px 8px;
          text-align: right; border-bottom: 0.5px solid rgba(0,0,0,0.1);
        }}
        .stock-table th:first-child {{ text-align: left; }}
        .stock-table td {{
          padding: 7px 6px; text-align: right;
          border-bottom: 0.5px solid rgba(0,0,0,0.06);
          color: inherit;
        }}
        .stock-table td:first-child {{ text-align: left; font-weight: 500; }}
        .stock-table tr:last-child td {{ border-bottom: none; }}

        /* Badges */
        .badge {{ display: inline-block; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 500; }}
        .badge.up {{ background: #EAF3DE; color: #3B6D11; }}
        .badge.down {{ background: #FAECE7; color: #993C1D; }}
        .badge.flat {{ background: #ebebea; color: #888780; }}

        /* Bar rows */
        .bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 9px; font-size: 12px; }}
        .bar-label {{ width: 90px; color: #888780; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0; }}
        .bar-track {{ flex: 1; height: 7px; background: #ebebea; border-radius: 4px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 4px; }}
        .bar-pct {{ width: 38px; text-align: right; font-weight: 500; flex-shrink: 0; }}

        /* Legend */
        .legend-row {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 12px; color: #888780; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }}

        /* Responsive */
        @media (max-width: 700px) {{
          .dash {{ padding: 12px; }}
          .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
          .grid2 {{ grid-template-columns: 1fr; }}
          .header {{ flex-direction: column; gap: 8px; }}
          .header-right {{ text-align: left; }}
        }}
        
        /* Hide default Streamlit elements */
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
    
    <div class="dash">
      <!-- Header -->
      <div class="header">
        <div class="header-left">
          <div class="sub">총 자산 (Hstock V1.1)</div>
          <div class="total">{int(real_total):,}원</div>
        </div>
        <div class="header-right">
          <div class="sub">투자 시작일</div>
          <div class="date">{invest_start} <span class="days">| {invest_days}</span></div>
        </div>
      </div>

      <!-- Metric Row 1 -->
      <div class="metric-grid">
        <div class="metric-card">
          <div class="metric-label">주식 평가금액</div>
          <div class="metric-value">{int(sm['eval']):,}</div>
          <div class="metric-sub">원</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">매수금액</div>
          <div class="metric-value">{int(sm['buy']):,}</div>
          <div class="metric-sub">원</div>
        </div>
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

      <!-- Metric Row 2 -->
      <div class="metric-grid">
        <div class="metric-card">
          <div class="metric-label">총 종목수</div>
          <div class="metric-value">{int(total_cnt)}</div>
          <div class="metric-sub">종목</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">수익 종목</div>
          <div class="metric-value up">{int(win_cnt)}</div>
          <div class="metric-sub up">{(win_cnt/total_cnt*100):.1f}%</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">손실 종목</div>
          <div class="metric-value down">{int(loss_cnt)}</div>
          <div class="metric-sub down">{(loss_cnt/total_cnt*100):.1f}%</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">누적 총수익</div>
          <div class="metric-value" style="font-size:17px;">{int(sm['accum']):,}</div>
          <div class="metric-sub">원</div>
        </div>
      </div>

      <!-- Main grid -->
      <div class="grid2">
        <!-- 종목 테이블 -->
        <div class="card">
          <div class="card-title">보유 종목 현황</div>
          <table class="stock-table">
            <thead>
              <tr><th>종목명</th><th>비중</th><th>현재가</th><th>평단가</th><th>수익률</th></tr>
            </thead>
            <tbody>
              {''.join([f"<tr><td>{r['Name']}</td><td>{r['Weight']}</td><td>{int(r['CurPrice']):,}</td><td>{int(r['AvgPrice']):,}</td><td><span class='badge {'up' if parse_numeric(r['Rate'])>=0 else 'down'}'>{r['Rate']}</span></td></tr>" for _, r in stocks.iterrows()])}
            </tbody>
          </table>
        </div>

        <!-- 우측 패널 -->
        <div style="display:flex;flex-direction:column;gap:16px;">
          <!-- 자산 유형별 -->
          <div class="card">
            <div class="card-title">자산 유형별 비중</div>
            {''.join([f"<div class='bar-row'><div class='bar-label'>{r[15]}</div><div class='bar-track'><div class='bar-fill' style='width:{parse_numeric(r[17])}%;background:{'#3266AD' if r[15]=='국내주식' else '#1D9E75' if r[15]=='안전자산' else '#7F77DD' if r[15]=='해외성장' else '#D85A30'};'></div></div><div class='bar-pct'>{r[17]}</div></div>" for _, r in df.iloc[1:5, 15:18].iterrows() if not pd.isna(r[15])])}
          </div>

          <!-- 증권사별 -->
          <div class="card">
            <div class="card-title">증권사별 비중</div>
            {''.join([f"<div class='bar-row'><div class='bar-label'>{r[11]}</div><div class='bar-track'><div class='bar-fill' style='width:{parse_numeric(r[12])}%;background:#3266AD;'></div></div><div class='bar-pct'>{r[12]}</div></div>" for _, r in df.iloc[1:15, 11:13].iterrows() if not pd.isna(r[11]) and r[11] not in ["비중", "증권사"]])}
          </div>
          
          <div class="card" style="padding: 12px 16px;">
            <div class="metric-label">현금 보유량</div>
            <div class="metric-value">{int(sm['cash']):,}원</div>
          </div>
        </div>
      </div>

      <!-- 수익금 차트 -->
      <div class="card" style="margin-bottom:0;">
        <div class="card-title">종목별 수익금 비교</div>
        <div class="legend-row">
          <div class="legend-item"><div class="legend-dot" style="background:#1D9E75;"></div>수익 종목</div>
          <div class="legend-item"><div class="legend-dot" style="background:#D85A30;"></div>손실 종목</div>
        </div>
        <div style="position:relative;width:100%;height:220px;">
          <canvas id="profitChart"></canvas>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Chart.js Script
    # Filtering for chart
    chart_stocks = stocks[stocks['Profit'] != 0].copy()
    chart_stocks['Profit'] = chart_stocks['Profit'].apply(parse_numeric)
    chart_stocks = chart_stocks.sort_values('Profit', ascending=False)
    
    js_labels = chart_stocks['Name'].tolist()
    js_data = chart_stocks['Profit'].tolist()
    js_colors = ['#1D9E75' if v >= 0 else '#D85A30' for v in js_data]

    st.components.v1.html(f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <div style="height: 220px;">
      <canvas id="pChart"></canvas>
    </div>
    <script>
      new Chart(document.getElementById('pChart'), {{
        type: 'bar',
        data: {{
          labels: {js_labels},
          datasets: [{{
            label: '수익금',
            data: {js_data},
            backgroundColor: {js_colors},
            borderRadius: 3,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: (ctx) => {{
                  const v = ctx.raw;
                  return (v >= 0 ? '+' : '') + v.toLocaleString('ko-KR') + '원';
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              ticks: {{ font: {{ size: 11 }}, color: '#888780', maxRotation: 30 }},
              grid: {{ display: false }},
            }},
            y: {{
              ticks: {{
                font: {{ size: 10 }},
                color: '#888780',
                callback: (v) => (v < 0 ? '-' : '') + Math.abs(v / 10000).toFixed(0) + '만'
              }},
              grid: {{ color: 'rgba(136,135,128,0.15)' }}
            }}
          }}
        }}
      }});
    </script>
    """, height=240)

else:
    st.error("데이터 로딩 실패")
