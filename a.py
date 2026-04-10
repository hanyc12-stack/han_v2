<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"/>
<meta name="theme-color" content="#0f172a"/>
<title>Hstock Premium Dashboard</title>

<!-- Fonts & Libs -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js"></script>

<style>
:root {
  --bg: #0f172a;
  --surface: #1e293b;
  --surface-hover: #334155;
  --card-bg: rgba(30, 41, 59, 0.7);
  --accent: #6366f1;
  --accent-light: #818cf8;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --border: rgba(255, 255, 255, 0.08);
  --up: #10b981;
  --up-bg: rgba(16, 185, 129, 0.1);
  --down: #ef4444;
  --down-bg: rgba(239, 68, 68, 0.1);
  --radius: 16px;
  --radius-sm: 8px;
  --shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

* { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
body {
  background: var(--bg);
  background-image: radial-gradient(circle at top right, rgba(99, 102, 241, 0.15), transparent),
                    radial-gradient(circle at bottom left, rgba(16, 185, 129, 0.1), transparent);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.5;
  min-height: 100vh;
  padding-bottom: 50px;
}

h1, h2, h3 { font-family: 'Outfit', sans-serif; }

.header {
  padding: 30px 20px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid var(--border);
}
.header-inner { max-width: 600px; margin: 0 auto; display: flex; justify-content: space-between; align-items: flex-end; }
.h-label { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.h-total { font-size: 28px; font-weight: 700; color: #fff; letter-spacing: -0.02em; }
.h-right { text-align: right; }
.h-date { font-size: 11px; color: var(--text-muted); display: block; margin-bottom: 2px; }
.h-days { font-size: 14px; font-weight: 600; color: var(--accent-light); }

.container { max-width: 600px; margin: 20px auto; padding: 0 16px; }

.metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
.metric-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  backdrop-filter: blur(6px);
  transition: transform 0.2s ease;
}
.metric-card:active { transform: scale(0.98); }
.m-label { font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 8px; }
.m-val { font-size: 20px; font-weight: 700; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.m-sub { font-size: 11px; margin-top: 4px; font-weight: 500; color: var(--text-muted); }

.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 20px;
  backdrop-filter: blur(6px);
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.card-title { font-size: 14px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

/* Table Styles */
.tbl-container { overflow-x: auto; margin: 0 -4px; }
.tbl { width: 100%; border-collapse: collapse; min-width: 300px; }
.tbl th { text-align: right; padding: 10px 8px; color: var(--text-muted); font-size: 11px; font-weight: 600; border-bottom: 1px solid var(--border); }
.tbl th:first-child { text-align: left; }
.tbl td { padding: 12px 8px; text-align: right; border-bottom: 1px dotted var(--border); font-size: 13px; vertical-align: middle; }
.tbl td:first-child { text-align: left; font-weight: 600; font-family: 'Outfit', sans-serif; color: #fff; }
.tbl tr:last-child td { border-bottom: none; }

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
}
.badge.up { background: var(--up-bg); color: var(--up); }
.badge.down { background: var(--down-bg); color: var(--down); }
.badge.flat { background: rgba(255,255,255,0.05); color: var(--text-muted); }

/* Bar Progress */
.bar-row { margin-bottom: 14px; }
.bar-info { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; font-weight: 500; }
.bar-name { color: var(--text); }
.bar-pct { color: var(--text-muted); }
.bar-track { height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 10px; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }

/* Utils */
.up { color: var(--up) !important; }
.down { color: var(--down) !important; }
.text-xs { font-size: 10px; }

.refresh-area { text-align: center; margin-top: 30px; }
.refresh-btn {
  background: var(--surface);
  border: 1px solid var(--border);
  color: #fff;
  padding: 10px 24px;
  border-radius: 30px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.refresh-btn:active { transform: scale(0.95); background: var(--surface-hover); }

.loader { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; }
.spinner { width: 40px; height: 40px; border: 3px solid rgba(99, 102, 241, 0.1); border-top: 3px solid var(--accent); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div>
      <div class="h-label">총 자산 총괄</div>
      <div class="h-total" id="h-total">—</div>
    </div>
    <div class="h-right">
      <span class="h-date" id="h-date">—</span>
      <span class="h-days" id="h-days">—</span>
    </div>
  </div>
</div>

<div class="container" id="loader-view">
  <div class="loader">
    <div class="spinner"></div>
    <div style="color:var(--text-muted)">HStock 엔진 부팅 중...</div>
  </div>
</div>

<div class="container" id="main-view" style="display:none">
  
  <div class="metric-grid">
    <div class="metric-card">
      <div class="m-label">주식 평가금</div>
      <div class="m-val" id="m-cur">—</div>
      <div class="m-sub">매수: <span id="m-buy">—</span></div>
    </div>
    <div class="metric-card">
      <div class="m-label">누적 수익금</div>
      <div class="m-val" id="m-profit">—</div>
      <div class="m-sub" id="m-rate">—</div>
    </div>
    <div class="metric-card">
      <div class="m-label">금일 변동액</div>
      <div class="m-val" id="m-daily">—</div>
      <div class="m-sub">변동률: <span id="m-daily-rate">—</span></div>
    </div>
    <div class="metric-card">
      <div class="m-label">총 종목 현황</div>
      <div class="m-val" id="m-total-cnt">—</div>
      <div class="m-sub">수익/손실: <span id="m-winloss">—</span></div>
    </div>
  </div>

  <div class="metric-grid" style="grid-template-columns: 1fr;">
    <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div class="m-label">현금 및 여유자금</div>
        <div class="m-val" id="m-cash">—</div>
      </div>
      <div style="text-align: right;">
        <div class="m-label">누적 총 수익</div>
        <div class="m-val" id="m-accum">—</div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><div class="card-title">수익금 TOP 비중</div></div>
    <div style="position:relative;width:100%;height:220px">
      <canvas id="profitChart"></canvas>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><div class="card-title">보유 종목 현황</div></div>
    <div class="tbl-container">
      <table class="tbl">
        <thead>
          <tr><th>종목명</th><th>비중</th><th>현재가</th><th>수익률</th></tr>
        </thead>
        <tbody id="stock-tbody"></tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><div class="card-title">자산 유형</div></div>
    <div id="asset-bars"></div>
  </div>

  <div class="card">
    <div class="card-header"><div class="card-title">보유 증권사</div></div>
    <div id="broker-bars"></div>
  </div>

  <div class="refresh-area">
    <button class="refresh-btn" onclick="init()">데이터 새로고침</button>
    <div style="font-size:10px; color:var(--text-muted); margin-top:12px;" id="last-update"></div>
  </div>

</div>

<script>
const SHEET_ID = "1WqEb6mn8eFH41mCj3BrrH_pSZMRECFR4qCHI1PmjeBg";
const SHEET_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=0`;

const ACCENTS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#f97316'];
const ASSET_MAP = {'국내주식': '#6366f1', '안전자산': '#10b981', '해외성장': '#8b5cf6', '가상화폐': '#f43f5e'};

let chart = null;

function parseNum(v) {
  if (typeof v !== 'string') return v || 0;
  return parseInt(v.replace(/[,%\s]/g, '')) || 0;
}

function fmt(n) { return n != null ? Math.round(n).toLocaleString() : '0'; }
function fmtS(n) { return (n >= 0 ? '+' : '') + fmt(n); }

async function init() {
  document.getElementById('loader-view').style.display = 'flex';
  document.getElementById('main-view').style.display = 'none';

  try {
    const res = await fetch(SHEET_URL);
    const csv = await res.text();
    Papa.parse(csv, {
      complete: (results) => render(results.data),
      error: (e) => alert("Parsing error: " + e.message)
    });
  } catch(e) {
    alert("Fetch error: " + e.message);
  }
}

function render(rows) {
  // 1. Stock Data (Domestic 2-9, US 12-15)
  const stocks = [];
  const stockRanges = [[1, 9], [11, 15]];
  stockRanges.forEach(range => {
    for (let i = range[0]; i < range[1]; i++) {
        const r = rows[i];
        if (!r || !r[0] || r[0].trim() === "현금" || r[0].trim() === "Total") continue;
        stocks.push({
            name: r[0].trim(),
            weight: r[1],
            qty: parseNum(r[2]),
            curAmt: parseNum(r[3]),
            buyAmt: parseNum(r[4]),
            profit: parseNum(r[5]),
            avgPrice: parseNum(r[6]),
            curPrice: parseNum(r[7]),
            rate: r[9]
        });
    }
  });

  // 2. Summary (Row 18)
  const sr = rows[17] || [];
  const cashRow = rows[17] || []; 
  const summary = {
    totalCur: parseNum(sr[3]),
    totalBuy: parseNum(sr[4]),
    profitAccum: parseNum(sr[5]),
    rateAccum: sr[6],
    dailyChg: parseNum(sr[7]),
    accumTotal: parseNum(sr[8]),
    totalAsset: parseNum(sr[13]),
    cash: parseNum(rows[17] ? rows[17][3] : 0)
  };

  // Adjust total asset if missing from col N
  const totalAsset = summary.totalAsset || (summary.totalCur + summary.cash);

  // 3. Brokers (L2-N15)
  const brokers = [];
  for(let i=1; i<15; i++){
    const r = rows[i];
    if(r && r[11] && r[11].trim() && r[11] !== "증권사"){
        brokers.push({ name: r[11].trim(), pct: parseFloat(r[12])||0 });
    }
  }

  // 4. Assets (P2-R5)
  const assets = [];
  for(let i=1; i<5; i++){
    const r = rows[i];
    if(r && r[15] && r[15].trim() && r[15] !== "자산유형"){
        assets.push({ name: r[15].trim(), pct: parseFloat(r[17])||0 });
    }
  }

  // UI Mapping
  document.getElementById('h-total').textContent = fmt(totalAsset) + '원';
  document.getElementById('h-date').textContent = rows[10] ? rows[10][20] : '';
  document.getElementById('h-days').textContent = rows[10] ? rows[10][22] : '';

  set('m-cur', fmt(summary.totalCur) + '원');
  set('m-buy', fmt(summary.totalBuy) + '원');
  
  const pEl = document.getElementById('m-profit');
  pEl.textContent = fmtS(summary.profitAccum) + '원';
  pEl.className = 'm-val ' + (summary.profitAccum >= 0 ? 'up' : 'down');
  
  const rEl = document.getElementById('m-rate');
  rEl.textContent = summary.rateAccum;
  rEl.className = 'm-sub ' + (parseFloat(summary.rateAccum) >= 0 ? 'up' : 'down');

  const dEl = document.getElementById('m-daily');
  dEl.textContent = fmtS(summary.dailyChg) + '원';
  dEl.className = 'm-val ' + (summary.dailyChg >= 0 ? 'up' : 'down');
  
  const dRate = ((summary.dailyChg / (summary.totalCur || 1)) * 100).toFixed(2);
  set('m-daily-rate', dRate + '%');
  document.getElementById('m-daily-rate').className = dRate >= 0 ? 'up' : 'down';

  set('m-total-cnt', stocks.length + '종목');
  const win = stocks.filter(s => s.profit > 0).length;
  const loss = stocks.filter(s => s.profit < 0).length;
  document.getElementById('m-winloss').innerHTML = `<span class="up">${win}</span> <span class="text-xs">승</span> / <span class="down">${loss}</span> <span class="text-xs">패</span>`;

  set('m-cash', fmt(summary.cash) + '원');
  set('m-accum', fmt(summary.accumTotal) + '원');

  // Table
  const tbody = document.getElementById('stock-tbody');
  tbody.innerHTML = '';
  stocks.forEach(s => {
    const rate = parseFloat(s.rate);
    const cls = rate > 0 ? 'up' : (rate < 0 ? 'down' : 'flat');
    tbody.innerHTML += `<tr>
        <td>${s.name}</td>
        <td class="text-xs">${s.weight}</td>
        <td>${fmt(s.curPrice)}</td>
        <td><span class="badge ${cls}">${rate > 0 ? '+' : ''}${s.rate}</span></td>
    </tr>`;
  });

  // Bar Progress
  const ab = document.getElementById('asset-bars'); ab.innerHTML = '';
  assets.forEach((a, i) => {
    ab.innerHTML += barComp(a.name, a.pct, ASSET_MAP[a.name] || ACCENTS[i % ACCENTS.length]);
  });

  const bb = document.getElementById('broker-bars'); bb.innerHTML = '';
  brokers.forEach((b, i) => {
    bb.innerHTML += barComp(b.name, b.pct, ACCENTS[i % ACCENTS.length]);
  });

  // Chart
  renderChart(stocks);

  document.getElementById('last-update').textContent = "마지막 동기화: " + new Date().toLocaleTimeString();
  document.getElementById('loader-view').style.display = 'none';
  document.getElementById('main-view').style.display = 'block';
}

function barComp(name, pct, color) {
  return `<div class="bar-row">
    <div class="bar-info"><span class="bar-name">${name}</span><span class="bar-pct">${pct.toFixed(1)}%</span></div>
    <div class="bar-track"><div class="bar-fill" style="width:${pct}%; background:${color}"></div></div>
  </div>`;
}

function renderChart(stocks) {
  const pStocks = stocks.filter(s => s.profit !== 0).sort((a,b) => b.profit - a.profit);
  const labels = pStocks.map(s => s.name);
  const data = pStocks.map(s => s.profit);
  const colors = data.map(v => v >= 0 ? '#10b981' : '#ef4444');

  if(chart) chart.destroy();
  chart = new Chart(document.getElementById('profitChart'), {
    type: 'bar',
    data: { labels, datasets: [{ data, backgroundColor: colors, borderRadius: 5 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 }, callback: v => (v/10000).toFixed(0) + '만' } }
      }
    }
  });
}

function set(id, val) { const el = document.getElementById(id); if(el) el.textContent = val; }

init();
</script>
</body>
</html>
