#!/usr/bin/env python3
"""
MK8s Financial Dashboard Generator v2 — Full Redesign
Reads three CSV exports and generates an enhanced dashboard with:
- 6 KPI cards (total, latest, MoM, active, churned, per-customer, savings plan)
- Revenue trend with MoM overlay
- SKU stacked area chart
- Top 10 customers + revenue concentration donut
- Units sold + revenue per unit
- Savings plan adoption trend
- Full customer table (all 500+)
"""

import sys, json, argparse, re
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
    from pandas.errors import EmptyDataError
except ImportError:
    sys.exit("ERROR: pandas required. pip install pandas")

def _months(df_raw, start_col):
    """Extract month column headers."""
    return [str(v).strip() for v in df_raw.iloc[0, start_col:]
            if pd.notna(v) and str(v).strip() and str(v).strip() != 'Reporting Date Dim: Month']

def _clean_number(s):
    """Parse currency string '€1,234.56' to float."""
    if pd.isna(s):
        return 0.0
    s = str(s).strip()
    # Remove € symbol, spaces, and commas
    s = re.sub(r'[€\s,]', '', s)
    try:
        return float(s) if s else 0.0
    except:
        return 0.0

def parse_rev_product(path):
    """Parse revenue by product CSV."""
    raw = pd.read_csv(path, header=None, dtype=str, encoding='utf-8-sig')
    months = _months(raw, 3)
    cols = ['item', 'unit', 'group'] + months
    df = raw.iloc[2:, :len(cols)].copy()
    df.columns = cols

    # Clean data
    df = df[df['item'].notna() & df['unit'].notna()]
    df = df[df['item'].str.strip().ne('') & df['unit'].str.strip().ne('')]
    for m in months:
        df[m] = df[m].apply(_clean_number)

    return df.reset_index(drop=True), months

def parse_rev_customer(path):
    """Parse revenue by customer CSV."""
    raw = pd.read_csv(path, header=None, dtype=str, encoding='utf-8-sig')
    months = _months(raw, 2)
    cols = ['contract_id', 'name'] + months
    df = raw.iloc[2:, :len(cols)].copy()
    df.columns = cols

    # Clean data
    df = df[df['contract_id'].notna() & df['contract_id'].str.strip().ne('')]
    for m in months:
        df[m] = df[m].apply(_clean_number)

    return df.reset_index(drop=True), months

def parse_quantities(path):
    """Parse quantities sold CSV."""
    raw = pd.read_csv(path, header=None, dtype=str, encoding='utf-8-sig')
    months = _months(raw, 3)
    cols = ['item', 'unit', 'group'] + months
    df = raw.iloc[2:, :len(cols)].copy()
    df.columns = cols

    # Clean data
    df = df[df['item'].notna() & df['unit'].notna()]
    df = df[df['item'].str.strip().ne('') & df['unit'].str.strip().ne('')]
    for m in months:
        df[m] = df[m].apply(_clean_number)

    return df.reset_index(drop=True), months

def aggregate(rp, rp_m, rc, rc_m, qs, qs_m):
    """Compute all KPIs and datasets for dashboard."""
    months = rp_m or rc_m or qs_m

    # Monthly revenue
    monthly_rev = [float(rp[m].sum()) if (not rp.empty and m in rp.columns) else 0.0
                   for m in months]

    # Revenue by group
    rev_by_group = {}
    if not rp.empty:
        for grp, g in rp.groupby('group'):
            rev_by_group[str(grp)] = [float(g[m].sum()) if m in g.columns else 0.0 for m in months]

    # Items (products)
    items = []
    if not rp.empty:
        for _, row in rp.iterrows():
            vals = [float(row.get(m, 0)) for m in months if m in rp.columns]
            items.append({
                'item': str(row['item']),
                'unit': str(row['unit']),
                'group': str(row['group']),
                'monthly': vals,
                'total': sum(vals),
            })
        items.sort(key=lambda x: x['total'], reverse=True)

    # Customers
    customers = []
    if not rc.empty:
        for _, row in rc.iterrows():
            vals = [float(row.get(m, 0)) for m in rc_m if m in rc.columns]
            customers.append({
                'id': str(row['contract_id']),
                'name': str(row['name']),
                'monthly': vals,
                'total': sum(vals),
            })
        customers.sort(key=lambda x: x['total'], reverse=True)

    # Quantities
    monthly_qty = [float(qs[m].sum()) if (not qs.empty and m in qs.columns) else 0.0
                   for m in months]

    # KPI calculations
    last_rev = monthly_rev[-1] if monthly_rev else 0.0
    prev_rev = monthly_rev[-2] if len(monthly_rev) >= 2 else 0.0
    mom = round((last_rev - prev_rev) / prev_rev * 100, 1) if prev_rev else None

    # Active contracts (customers with revenue in last 3 months)
    active = sum(1 for c in customers if sum(c['monthly'][-3:]) > 0) if customers else 0

    # Churned contracts (had revenue earlier but not in last 3 months)
    churned = sum(1 for c in customers
                  if sum(c['monthly'][:-3]) > 0 and sum(c['monthly'][-3:]) == 0) if customers else 0

    # Revenue per customer
    avg_rev_per_cust = sum(c['total'] for c in customers) / active if active > 0 else 0

    # Savings plan revenue
    savings_items = [i for i in items if 'savings' in i['item'].lower() or 'spk' in i['item'].lower()]
    savings_revenue = sum(i['total'] for i in savings_items)

    # Revenue per unit (by SKU)
    revenue_per_unit = {}
    qty_df = qs if not qs.empty else pd.DataFrame()
    for item in items:
        item_name = item['item']
        qty_row = qty_df[qty_df['item'] == item_name] if not qty_df.empty else None
        if qty_row is not None and not qty_row.empty:
            total_qty = sum(float(qty_row[m].iloc[0]) if m in qty_row.columns else 0 for m in months)
            if total_qty > 0:
                revenue_per_unit[item_name] = round(item['total'] / total_qty, 6)

    # Savings plan time series (4 SKUs)
    sp_skus = {'SPKC1000', 'SPKC3000', 'SPKR1000', 'SPKR3000'}
    sp_monthly = {}
    for sku in sp_skus:
        sku_item = next((i for i in items if i['item'] == sku), None)
        if sku_item:
            sp_monthly[sku] = sku_item['monthly']

    return {
        'months': months,
        'monthly_revenue': monthly_rev,
        'revenue_by_group': rev_by_group,
        'items': items,
        'customers': customers,
        'cust_months': rc_m,
        'monthly_quantities': monthly_qty,
        'revenue_per_unit': revenue_per_unit,
        'savings_monthly': sp_monthly,
        'kpis': {
            'total_revenue': sum(monthly_rev),
            'latest_month': months[-1] if months else None,
            'latest_revenue': last_rev,
            'mom_growth': mom,
            'active_contracts': active,
            'churned_contracts': churned,
            'avg_revenue_per_customer': avg_rev_per_cust,
            'savings_plan_revenue': savings_revenue,
            'total_units': sum(monthly_qty),
        },
    }

HTML_TEMPLATE_START = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MK8s Financial Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0E1624;--card:#162035;--border:#1E2D4A;
  --text:#E8EFF8;--muted:#8899B4;
  --blue:#003D8F;--blue2:#1565C0;--amber:#FFAA00;
  --green:#00C896;--red:#FF4B6B
}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh}
.hdr{padding:20px 32px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.hdr h1{font-size:20px;font-weight:700}.hdr h1 span{color:var(--amber)}
.hdr .meta{font-size:12px;color:var(--muted)}
.main{padding:24px 32px}
.kpi-row{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-bottom:24px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 20px}
.kpi .lbl{font-size:10px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.kpi .val{font-size:24px;font-weight:700;line-height:1;margin-bottom:4px}
.kpi .sub{font-size:12px;color:var(--muted)}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:600;margin-top:6px}
.badge.pos{background:rgba(0,200,150,.15);color:var(--green)}
.badge.neg{background:rgba(255,75,107,.15);color:var(--red)}
.ch-full{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:24px}
.ch-2col{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}
.ch-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px}
.ch-title{font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);margin-bottom:14px}
.cw-tall{position:relative;height:280px}
.cw-med{position:relative;height:220px}
.tbl-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:24px}
.tbl-card h3{font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
.search{width:100%;padding:8px 12px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;margin-bottom:12px;outline:none}
.search:focus{border-color:var(--blue2)}
.dt{width:100%;border-collapse:collapse;font-size:13px}
.dt th{text-align:left;padding:7px 10px;color:var(--muted);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid var(--border)}
.dt td{padding:7px 10px;border-bottom:1px solid rgba(30,45,74,.5)}
.dt tr:last-child td{border-bottom:none}
.dt tr:hover td{background:rgba(255,255,255,.025)}
.dt td.r{text-align:right;font-variant-numeric:tabular-nums;color:var(--amber);font-weight:600}
.dt td.m{color:var(--muted)}
.pill{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:rgba(0,61,143,.25);color:#6699FF}
.empty{text-align:center;padding:48px 20px;color:var(--muted)}
.empty .ico{font-size:32px;margin-bottom:10px}
.ovx{overflow-x:auto}
.data-note{font-size:11px;color:var(--muted);margin-top:8px}
@media(max-width:1400px){.kpi-row{grid-template-columns:repeat(3,1fr)}}
@media(max-width:900px){.kpi-row{grid-template-columns:repeat(2,1fr)}.ch-2col{grid-template-columns:1fr}}
</style>
</head>
<body>
<header class="hdr">
  <h1>MK8s <span>Financial Dashboard</span></h1>
  <div class="meta" id="meta-range"></div>
</header>
<main class="main">
  <!-- 6 KPI Cards -->
  <div class="kpi-row">
    <div class="kpi"><div class="lbl">Total Revenue</div><div class="val" id="k-total">—</div><div class="sub" id="k-range">—</div></div>
    <div class="kpi"><div class="lbl">Latest Month</div><div class="val" id="k-latest">—</div><div class="sub" id="k-month">—</div></div>
    <div class="kpi"><div class="lbl">MoM Growth</div><div class="val" id="k-mom">—</div><div id="k-mom-badge"></div></div>
    <div class="kpi"><div class="lbl">Active Contracts</div><div class="val" id="k-active">—</div><div class="sub">last 3 months</div></div>
    <div class="kpi"><div class="lbl">Churned Contracts</div><div class="val" id="k-churned">—</div><div class="sub">lost revenue</div></div>
    <div class="kpi"><div class="lbl">Revenue per Customer</div><div class="val" id="k-rpc">—</div><div class="sub">annual average</div></div>
  </div>

  <!-- Monthly Revenue Trend with MoM -->
  <div class="ch-full">
    <div class="ch-title">Monthly Revenue Trend (€ + MoM %)</div>
    <div class="cw-tall"><canvas id="c-trend"></canvas></div>
    <div class="data-note">March 2026 is partial month</div>
  </div>

  <!-- Revenue by SKU (Stacked Area) + Concentration Donut -->
  <div class="ch-2col">
    <div class="ch-box">
      <div class="ch-title">Revenue by SKU (Stacked Area)</div>
      <div class="cw-tall" id="wrap-area"><canvas id="c-area"></canvas></div>
    </div>
    <div class="ch-box">
      <div class="ch-title">Revenue Concentration</div>
      <div class="cw-tall" id="wrap-conc"><canvas id="c-concentration"></canvas></div>
    </div>
  </div>

  <!-- Units Sold + Revenue per Unit -->
  <div class="ch-2col">
    <div class="ch-box">
      <div class="ch-title">Units Sold by Month</div>
      <div class="cw-tall"><canvas id="c-qty"></canvas></div>
      <div class="data-note">March 2026 is partial month</div>
    </div>
    <div class="ch-box">
      <div class="ch-title">Revenue per Unit by SKU (€/unit)</div>
      <div class="cw-tall"><canvas id="c-rpu"></canvas></div>
    </div>
  </div>

  <!-- Savings Plan Adoption -->
  <div class="ch-full">
    <div class="ch-title">Savings Plan Revenue Trend</div>
    <div class="cw-med"><canvas id="c-savings"></canvas></div>
    <div class="data-note">4 SKUs: SPKC1000, SPKC3000, SPKR1000, SPKR3000 — commitment-based pricing</div>
  </div>

  <!-- Top 10 Customers -->
  <div class="ch-full">
    <div class="ch-title">Top 10 Customers by Revenue</div>
    <div class="cw-tall"><canvas id="c-topcust"></canvas></div>
  </div>

  <!-- Product Table -->
  <div class="tbl-card">
    <h3>Product Revenue Breakdown (All 10 SKUs)</h3>
    <div id="prod-tbl"></div>
  </div>

  <!-- Customer Table -->
  <div class="tbl-card">
    <h3>Customer Revenue Detail (All 500+ Customers)</h3>
    <input class="search" id="cust-q" type="text" placeholder="Search by company name or contract ID…" oninput="filterCust()">
    <div id="cust-tbl"></div>
  </div>
</main>

<script>
const D = __DATA__;

const eur = v => new Intl.NumberFormat('de-DE',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(v);
const n   = v => new Intl.NumberFormat('de-DE').format(Math.round(v));
const pct = v => (v >= 0 ? '+' : '') + v.toFixed(1) + '%';
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

const P = ['#003D8F','#FFAA00','#00C896','#FF6B6B','#9B59B6','#00B4D8','#F28C28','#2ECC71','#E74C3C','#1ABC9C'];
const GX = {ticks:{color:'#8899B4',font:{size:11}},grid:{color:'rgba(30,45,74,.6)'}};
const GY = {ticks:{color:'#8899B4',font:{size:11}},grid:{color:'rgba(30,45,74,.6)'}};
const GL = {labels:{color:'#8899B4',font:{size:12},boxWidth:12}};

function emptyHTML(msg){return '<div class="empty"><div class="ico">📊</div><p>'+msg+'</p></div>';}

// ── KPIs ──────────────────────────────────────────────────────────────────────
function initKPIs(){
  const k = D.kpis, m = D.months;
  const range = m.length ? m[0]+' – '+m[m.length-1] : '—';
  document.getElementById('meta-range').textContent = range;
  document.getElementById('k-total').textContent = eur(k.total_revenue);
  document.getElementById('k-range').textContent = range;
  document.getElementById('k-latest').textContent = eur(k.latest_revenue);
  document.getElementById('k-month').textContent = k.latest_month || '—';
  document.getElementById('k-active').textContent = n(k.active_contracts);
  document.getElementById('k-churned').textContent = n(k.churned_contracts);
  document.getElementById('k-rpc').textContent = eur(k.avg_revenue_per_customer);

  if(k.mom_growth !== null && k.mom_growth !== undefined){
    document.getElementById('k-mom').textContent = pct(k.mom_growth);
    const pos = k.mom_growth >= 0;
    document.getElementById('k-mom-badge').innerHTML =
      '<span class="badge '+(pos?'pos':'neg')+'">'+(pos?'▲':'▼')+' vs prev</span>';
  } else {
    document.getElementById('k-mom').textContent = '—';
  }
}

// ── Revenue Trend with MoM ─────────────────────────────────────────────────────
function initTrend(){
  const rev = D.monthly_revenue;
  const mom_vals = [];
  for(let i = 0; i < rev.length; i++){
    if(i === 0) mom_vals.push(null);
    else mom_vals.push((rev[i] - rev[i-1]) / rev[i-1] * 100);
  }

  new Chart(document.getElementById('c-trend'),{
    type:'line',
    data:{
      labels:D.months,
      datasets:[
        {
          label:'€ Revenue',data:rev,yAxisID:'y',
          borderColor:'#003D8F',backgroundColor:'rgba(0,61,143,.12)',fill:true,
          tension:.35,pointBackgroundColor:'#FFAA00',pointRadius:4,pointHoverRadius:6,borderWidth:2
        },
        {
          label:'MoM %',data:mom_vals,yAxisID:'y1',
          type:'bar',backgroundColor:'rgba(255,170,0,.2)',borderColor:'#FFAA00',borderWidth:0
        }
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:GL,tooltip:{mode:'index',intersect:false}},
      scales:{
        x:GX,
        y:{type:'linear',position:'left',ticks:{color:'#8899B4',font:{size:11},callback:v=>eur(v)},grid:{color:'rgba(30,45,74,.6)'}},
        y1:{type:'linear',position:'right',ticks:{color:'#FFAA00',font:{size:11},callback:v=>v.toFixed(1)+'%'},grid:{display:false}}
      }
    }
  });
}

// ── SKU Stacked Area ────────────────────────────────────────────────────────────
function initArea(){
  const wrap = document.getElementById('wrap-area');
  const items = D.items.slice(0,10);
  if(!items.length){wrap.innerHTML=emptyHTML('No SKU data');return;}

  const datasets = items.map((item, i) => ({
    label: item.item,
    data: item.monthly,
    borderColor: P[i],
    backgroundColor: P[i] + '33',
    borderWidth: 1,
    fill: true,
    tension: 0.2
  }));

  new Chart(document.getElementById('c-area'),{
    type: 'line',
    data: {labels: D.months, datasets: datasets},
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {legend: GL, tooltip: {callbacks: {label: c => ' '+c.dataset.label+': '+eur(c.parsed.y)}}},
      scales: {
        x: GX,
        y: {
          stacked: true,
          ticks: {color:'#8899B4',font:{size:11},callback:v=>eur(v)},
          grid:{color:'rgba(30,45,74,.6)'}
        }
      }
    }
  });
}

// ── Revenue Concentration Donut ────────────────────────────────────────────────
function initConcentration(){
  const wrap = document.getElementById('wrap-conc');
  const custs = D.customers || [];
  if(!custs.length){wrap.innerHTML=emptyHTML('No customer data');return;}

  const top10_rev = custs.slice(0,10).reduce((s,c)=>s+c.total,0);
  const next40_rev = custs.slice(10,50).reduce((s,c)=>s+c.total,0);
  const rest_rev = custs.slice(50).reduce((s,c)=>s+c.total,0);
  const total = top10_rev + next40_rev + rest_rev;

  new Chart(document.getElementById('c-concentration'),{
    type:'doughnut',
    data:{
      labels:['Top 10 (10 cust)','Next 40 (40 cust)','Rest ('+Math.max(0,custs.length-50)+' cust)'],
      datasets:[{
        data:[top10_rev/total*100,next40_rev/total*100,rest_rev/total*100],
        backgroundColor:['#FFAA00','#003D8F','#1E2D4A'],
        borderColor:'#0E1624',borderWidth:2
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:GL,
        tooltip:{callbacks:{label:c=>' '+c.label+': '+c.parsed+'%'}}
      }
    }
  });
}

// ── Units Sold ────────────────────────────────────────────────────────────────
function initQty(){
  new Chart(document.getElementById('c-qty'),{
    type:'line',
    data:{
      labels:D.months,
      datasets:[{
        label:'Units Sold',data:D.monthly_quantities,
        borderColor:'#00C896',backgroundColor:'rgba(0,200,150,.1)',fill:true,
        tension:.35,pointBackgroundColor:'#00C896',pointRadius:4,borderWidth:2
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:GL,tooltip:{callbacks:{label:c=>' '+n(c.parsed.y)+' units'}}},
      scales:{x:GX,y:GY}
    }
  });
}

// ── Revenue per Unit ───────────────────────────────────────────────────────────
function initRPU(){
  const wrap = document.getElementById('wrap-conc').parentElement.parentElement;
  const rpu = D.revenue_per_unit || {};
  const labels = Object.keys(rpu).slice(0,10);
  if(!labels.length){return;}
  const data = labels.map(sku => rpu[sku]);

  new Chart(document.getElementById('c-rpu'),{
    type:'bar',
    data:{
      labels:labels,
      datasets:[{
        label:'€/unit',data:data,
        backgroundColor:labels.map((_,i)=>P[i%P.length])
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' €'+c.parsed.y.toFixed(4)+'/unit'}}},
      scales:{
        x:GX,
        y:{ticks:{color:'#8899B4',font:{size:11}},grid:{color:'rgba(30,45,74,.6)'}}
      }
    }
  });
}

// ── Savings Plan Adoption ──────────────────────────────────────────────────────
function initSavings(){
  const sp = D.savings_monthly || {};
  const skus = ['SPKC1000','SPKC3000','SPKR1000','SPKR3000'];
  const datasets = skus.map((sku,i) => ({
    label:sku,
    data:sp[sku]||[],
    borderColor:P[i],
    backgroundColor:P[i]+'33',
    fill:false,
    tension:.35,
    pointRadius:3,
    borderWidth:2
  }));

  new Chart(document.getElementById('c-savings'),{
    type:'line',
    data:{labels:D.months,datasets:datasets},
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:GL,tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+eur(c.parsed.y)}}},
      scales:{x:GX,y:{ticks:{color:'#8899B4',font:{size:11},callback:v=>eur(v)},grid:{color:'rgba(30,45,74,.6)'}}}
    }
  });
}

// ── Top 10 Customers ───────────────────────────────────────────────────────────
function initTopCust(){
  const top = (D.customers||[]).slice(0,10);
  if(!top.length){document.getElementById('wrap-topcust').innerHTML=emptyHTML('No customer data');return;}

  new Chart(document.getElementById('c-topcust'),{
    type:'bar',
    data:{
      labels:top.map(c=>c.name.length>32?c.name.slice(0,32)+'…':c.name),
      datasets:[{
        label:'Total Revenue',
        data:top.map(c=>c.total),
        backgroundColor:top.map((_,i)=>'rgba(255,170,0,'+Math.max(.3,1-i*.08)+')'),
        borderRadius:3
      }]
    },
    options:{
      indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' '+eur(c.parsed.x)}}},
      scales:{
        x:{ticks:{color:'#8899B4',font:{size:11},callback:v=>eur(v)},grid:{color:'rgba(30,45,74,.6)'}},
        y:GY
      }
    }
  });
}

// ── Product Table ──────────────────────────────────────────────────────────────
function initProdTable(){
  const el = document.getElementById('prod-tbl');
  if(!D.items.length){el.innerHTML=emptyHTML('No product data');return;}
  const m = D.months, show = m.slice(-3);
  let h = '<div class="ovx"><table class="dt"><thead><tr><th>SKU</th><th>Unit</th><th>Group</th>';
  show.forEach(x=>h+='<th class="r">'+x+'</th>');
  h+='<th class="r">Total</th></tr></thead><tbody>';
  D.items.forEach(item=>{
    const vals = show.map(x=>{const i=m.indexOf(x);return i>=0?(item.monthly[i]||0):0;});
    h+='<tr><td><strong>'+esc(item.item)+'</strong></td><td class="m">'+esc(item.unit)+'</td>';
    h+='<td><span class="pill">'+esc(item.group)+'</span></td>';
    vals.forEach(v=>h+='<td class="r">'+eur(v)+'</td>');
    h+='<td class="r"><strong>'+eur(item.total)+'</strong></td></tr>';
  });
  el.innerHTML=h+'</tbody></table></div>';
}

// ── Customer Table ────────────────────────────────────────────────────────────
let _custs=[];
function initCustTable(){_custs=D.customers||[];renderCusts(_custs);}
function filterCust(){
  const q=document.getElementById('cust-q').value.toLowerCase();
  renderCusts(q?_custs.filter(c=>c.name.toLowerCase().includes(q)||c.id.toLowerCase().includes(q)):_custs);
}
function renderCusts(list){
  const el=document.getElementById('cust-tbl');
  if(!list.length){el.innerHTML=emptyHTML('No results');return;}
  const m=D.cust_months||D.months, show=m.slice(-3);
  let h='<div class="ovx"><table class="dt"><thead><tr><th>Contract ID</th><th>Company</th>';
  show.forEach(x=>h+='<th class="r">'+x+'</th>');
  h+='<th class="r">Total</th></tr></thead><tbody>';
  list.forEach(c=>{
    const vals=show.map(x=>{const i=m.indexOf(x);return i>=0?(c.monthly[i]||0):0;});
    h+='<tr><td class="m">'+esc(c.id)+'</td><td>'+esc(c.name)+'</td>';
    vals.forEach(v=>h+='<td class="r">'+eur(v)+'</td>');
    h+='<td class="r"><strong>'+eur(c.total)+'</strong></td></tr>';
  });
  el.innerHTML=h+'</tbody></table></div>';
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  initKPIs();
  if(D.months.length){
    initTrend();
    initArea();
    initConcentration();
    initQty();
    initRPU();
    initSavings();
  }
  initTopCust();
  initProdTable();
  initCustTable();
});
</script>
</body>
</html>
"""

def generate_html(data):
    """Embed data into HTML template."""
    return HTML_TEMPLATE.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))

def _classify(path: Path):
    """Classify CSV by filename."""
    name = path.name.lower()
    if 'customer' in name:
        return 'revenue_customer'
    if 'quantit' in name:
        return 'quantities'
    return 'revenue_product'

def resolve_files(inputs: list[str]) -> dict:
    """Resolve input paths to files."""
    if not inputs:
        inputs = ['.']

    if len(inputs) == 1 and Path(inputs[0]).is_dir():
        directory = Path(inputs[0]).resolve()
        candidates = sorted(directory.glob('*.csv'))
        mk8s = [f for f in candidates if 'mk8s' in f.name.lower()]
        if not mk8s:
            mk8s = candidates
        found = {}
        for f in mk8s:
            role = _classify(f)
            if role not in found:
                found[role] = f
        return found

    found = {}
    for raw in inputs:
        p = Path(raw).resolve()
        if not p.exists():
            sys.exit(f"ERROR: file not found: {p}")
        role = _classify(p)
        if role in found:
            sys.exit(f"ERROR: two files classified as '{role}'")
        found[role] = p
    return found

def main():
    ap = argparse.ArgumentParser(description='Generate MK8s financial dashboard v2 (full redesign)')
    ap.add_argument('paths', nargs='*', metavar='PATH',
                    help='Directory containing CSVs, or up to 3 explicit file paths')
    ap.add_argument('--output', default='mk8s-financial-dashboard.html',
                    help='Output HTML file')
    args = ap.parse_args()

    files = resolve_files(args.paths)

    required = {'revenue_product', 'revenue_customer', 'quantities'}
    missing = required - files.keys()
    if missing:
        print("ERROR: missing files:")
        for role in missing:
            print(f"  • {role}")
        sys.exit(1)

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = files['revenue_product'].parent / out_path

    print("Parsing CSVs...")
    rp, rp_m = parse_rev_product(files['revenue_product'])
    rc, rc_m = parse_rev_customer(files['revenue_customer'])
    qs, qs_m = parse_quantities(files['quantities'])
    print(f"  Products: {len(rp)} | Customers: {len(rc)} | Quantities items: {len(qs)}")

    print("Aggregating data & computing KPIs...")
    data = aggregate(rp, rp_m, rc, rc_m, qs, qs_m)

    print("Generating HTML...")
    html = generate_html(data)
    out_path.write_text(html, encoding='utf-8')

    print(f"✓ Dashboard saved to: {out_path}")
    print(f'  Open with: open "{out_path}"')

if __name__ == '__main__':
    main()
