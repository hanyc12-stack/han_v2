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
    # 진단용 출력
    # st.write("Brokerage 데이터 확인:", df.iloc[0:20, 11:14])
    
    # 헬퍼: V열(21)에서 항목명을 찾아 W열(22) 또는 X열(23) 값을 가져옴
    def get_summary_val(label, col_target=22):
        try:
            # V열에서 label이 포함된 행 찾기
            row = df[df[21].astype(str).str.contains(label, na=False)]
            if not row.empty:
                val = row.iloc[0, col_target]
                return val if pd.notna(val) else "0"
            return "0"
        except:
            return "0"

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

    # 상단 요약 지표 (V~X열 다이나믹 매핑)
    sm = {
        "eval":   parse_numeric(get_summary_val("주식 평가금액", 22)), # W열
        "buy":    parse_numeric(get_summary_val("매수금액", 22)),     # W열
        "profit": parse_numeric(get_summary_val("누적 수익금", 22)),   # W열
        "rate":   str(get_summary_val("누적 수익금", 23)),             # X열 (수익률)
        "daily":  parse_numeric(get_summary_val("금일 변동액", 22)),   # W열
        "daily_rate": str(get_summary_val("금일 변동액", 23)),         # X열 (변동률)
        "cash":   parse_numeric(get_summary_val("현금 보유량", 22)),   # W열
    }
    
    # 실시간 데이터 진단 (임시 추가)
    # st.write("V-X 영역 관찰:", df.iloc[0:15, 21:24])

    # 총 자산 계산 (Q6 참조 혹은 평가금+현금)
    total_asset_q6 = parse_numeric(df.iloc[5, 16]) 
    real_total = total_asset_q6 if total_asset_q6 > 0 else (sm["eval"] + sm["cash"])

    invest_start = str(df.iloc[11, 15])           # P12: 투자 시작일
    invest_days = str(df.iloc[11, 17])            # R12: 투자일/경과일

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
            <span style="font-size:15px; font-weight:500; margin-left:4px;">({sm['rate'] if sm['rate'] != '0' else '-%'})</span>
          </div>
          <div class="metric-sub">원</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">금일 변동액</div>
          <div class="metric-value {get_color_class(sm['daily'])}">
            {int(sm['daily']):+,}
            <span style="font-size:15px; font-weight:500; margin-left:4px;">({sm['daily_rate'] if sm['daily_rate'] != '0' else '-%'})</span>
          </div>
          <div class="metric-sub">원</div>
        </div>
        <div class="metric-card"><div class="metric-label">현금 보유량</div><div class="metric-value">{int(sm['cash']):,}</div><div class="metric-sub">원</div></div>
      </div>

      <div class="card" style="width: 100%; margin-bottom: 24px;">
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

    # --- 차트 섹션 (st.components.v1.html 사용으로 안정성 확보) ---
    import streamlit.components.v1 as components
    import json

    # 데이터 준비
    stock_labels = stocks['Name'].tolist()
    stock_values = [parse_numeric(w) for w in stocks['Weight']]
    
    # 증권사 데이터 추출 (필터링 강화)
    br_df = df.iloc[1:20, [11, 12]].copy()
    br_df.columns = ['Name', 'Weight']
    br_clean = br_df[
        br_df['Name'].notna() & 
        (~br_df['Name'].astype(str).str.contains("증권사|Total|합계", case=False)) &
        (br_df['Weight'].notna())
    ]
    br_labels = br_clean['Name'].tolist()
    br_values = [parse_numeric(w) for w in br_clean['Weight']]

    chart_html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; background: transparent; margin: 0; padding: 0; overflow: hidden; }}
        .chart-container {{ display: flex; gap: 24px; padding: 10px; }}
        .card {{ 
            background: #fff; border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; 
            padding: 24px; width: 48%; box-shadow: 0 4px 15px rgba(0,0,0,0.04);
            height: 380px; box-sizing: border-box;
        }}
        .card-title {{ font-size: 17px; font-weight: 700; color: #1a1a18; margin-bottom: 20px; }}
        canvas {{ max-height: 280px; }}
        @media (prefers-color-scheme: dark) {{
            .card {{ background: #242422; border-color: rgba(255,255,255,0.1); }}
            .card-title {{ color: #e8e6df; }}
        }}
    </style>
    <div class="chart-container">
        <div class="card">
            <div class="card-title">📊 종목별 비중</div>
            <canvas id="stockChart"></canvas>
        </div>
        <div class="card">
            <div class="card-title">🏢 증권사별 비중</div>
            <canvas id="brokerChart"></canvas>
        </div>
    </div>
    <script>
        const colors = ['#E57373', '#64B5F6', '#81C784', '#FFF176', '#FFB74D', '#BA68C8', '#A1887F', '#90A4AE', '#4DB6AC', '#AED581'];
        const createCfg = (labels, data) => ({{
            type: 'doughnut',
            data: {{
                labels: labels,
                datasets: [{{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0,
                    hoverOffset: 12
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right', labels: {{ padding: 15, font: {{ size: 12 }} }} }},
                    tooltip: {{ enabled: true }}
                }},
                cutout: '65%'
            }}
        }});
        new Chart(document.getElementById('stockChart'), createCfg({json.dumps(stock_labels)}, {json.dumps(stock_values)}));
        new Chart(document.getElementById('brokerChart'), createCfg({json.dumps(br_labels)}, {json.dumps(br_values)}));
    </script>
    """
    components.html(chart_html, height=420)
else:
    st.error("데이터 로딩 실패")
