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
    # --- 차트 섹션 (st.components.v1.html 사용으로 안정성 확보) ---
    import streamlit.components.v1 as components
    import json

    # 1. 종목 비중 데이터
    stock_names = stocks['Name'].tolist()
    stock_weights = [parse_numeric(w) for w in stocks['Weight']]
    
    # 2. 종목 수익금 데이터
    # 누적수익금(Profit) 데이터를 숫자형으로 파싱
    stock_profits = [parse_numeric(p) for p in stocks['Profit']]

    chart_html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; background: transparent; margin: 0; padding: 0; overflow-x: hidden; }}
        .visual-container {{ display: flex; flex-direction: column; gap: 24px; padding: 10px; }}
        .card {{ 
            background: #fff; border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; 
            padding: 24px; width: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.04);
            box-sizing: border-box;
        }}
        .card-title {{ font-size: 17px; font-weight: 700; color: #1a1a18; margin-bottom: 20px; }}
        @media (prefers-color-scheme: dark) {{
            .card {{ background: #242422; border-color: rgba(255,255,255,0.1); }}
            .card-title {{ color: #e8e6df; }}
        }}
    </style>
    <div class="visual-container">
        <div class="card">
            <div class="card-title">📊 종목별 비중</div>
            <div style="height: 320px;"><canvas id="weightChart"></canvas></div>
        </div>
        <div class="card">
            <div class="card-title">💵 종목별 수익금 비교 (누적수익금)</div>
            <div style="height: 400px;"><canvas id="profitChart"></canvas></div>
        </div>
    </div>
    <script>
        Chart.register(ChartDataLabels);
        const palette = ['#E57373', '#64B5F6', '#81C784', '#FFF176', '#FFB74D', '#BA68C8', '#A1887F', '#90A4AE', '#4DB6AC', '#AED581'];
        
        // 1. 비중 도넛 차트
        new Chart(document.getElementById('weightChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(stock_names)},
                datasets: [{{
                    data: {json.dumps(stock_weights)},
                    backgroundColor: palette,
                    borderWidth: 0,
                    hoverOffset: 12
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right', labels: {{ padding: 12, font: {{ size: 12 }} }} }},
                    datalabels: {{
                        color: '#fff',
                        font: {{ weight: 'bold', size: 11 }},
                        formatter: (val) => val > 2 ? val.toFixed(1) + '%' : '',
                        anchor: 'center', align: 'center',
                        textShadowBlur: 2, textShadowColor: 'rgba(0,0,0,0.3)'
                    }},
                    tooltip: {{ enabled: true }}
                }},
                cutout: '65%'
            }}
        }});

        // 2. 수익금 바 차트
        const profitVals = {json.dumps(stock_profits)};
        new Chart(document.getElementById('profitChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(stock_names)},
                datasets: [{{
                    label: '누적수익금',
                    data: profitVals,
                    backgroundColor: profitVals.map(v => v >= 0 ? '#D85A30' : '#3266AD'),
                    borderRadius: 6,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{ 
                        grid: {{ color: 'rgba(0,0,0,0.05)' }},
                        ticks: {{ font: {{ family: 'Noto Sans KR' }} }}
                    }},
                    y: {{ 
                        grid: {{ display: false }},
                        ticks: {{ font: {{ weight: 'bold', family: 'Noto Sans KR' }} }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    datalabels: {{
                        anchor: 'end',
                        align: 'end',
                        color: (ctx) => ctx.dataset.data[ctx.dataIndex] >= 0 ? '#D85A30' : '#3266AD',
                        font: {{ weight: 'bold', size: 11 }},
                        formatter: (val) => Math.abs(val) >= 1000 ? (val/10000).toFixed(1) + '만' : val
                    }}
                }}
            }}
        }});
    </script>
    """
    components.html(chart_html, height=850)
else:
    st.error("데이터 로딩 실패")
