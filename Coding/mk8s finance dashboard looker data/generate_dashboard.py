#!/usr/bin/env python3
"""
MK8s Financial Dashboard Generator

Reads three CSV exports and generates a self-contained HTML dashboard.

Usage:
    python generate_dashboard.py
    python generate_dashboard.py --data-dir /path/to/csvs --output dashboard.html

Expected CSVs (in --data-dir):
    • Revenue Revenue Projection-MK8s.csv
    • Customers Revenue Revenue Projection mk8s.csv
    • Quantities Sold mk8s.csv
"""

import sys, json, argparse
from pathlib import Path

try:
    import pandas as pd
    from pandas.errors import EmptyDataError
except ImportError:
    sys.exit("ERROR: pandas is required.\n  pip install pandas")

REV_PRODUCT_FILE  = "Revenue Revenue Projection-MK8s.csv"
REV_CUSTOMER_FILE = "Customers Revenue Revenue Projection mk8s.csv"
QUANTITIES_FILE   = "Quantities Sold mk8s.csv"
DEFAULT_OUTPUT    = "mk8s-financial-dashboard.html"


# ── Parsers ────────────────────────────────────────────────────────────────────

def _months(df_raw, start_col):
    return [str(v).strip() for v in df_raw.iloc[0, start_col:]
            if pd.notna(v) and str(v).strip()]

def _num(series):
    return pd.to_numeric(
        series.astype(str).str.replace(r'[\s,\xa0]', '', regex=True),
        errors='coerce'
    ).fillna(0.0)

def _read_data(path, skiprows, cols):
    """Read data rows; return empty DataFrame if file has only headers."""
    try:
        df = pd.read_csv(path, skiprows=skiprows, header=None, dtype=str, encoding='utf-8-sig')
    except EmptyDataError:
        return pd.DataFrame(columns=cols)
    if df.empty:
        return pd.DataFrame(columns=cols)
    df = df.iloc[:, :len(cols)]
    df.columns = cols
    return df

def parse_rev_product(path):
    raw    = pd.read_csv(path, header=None, dtype=str, encoding='utf-8-sig')
    months = _months(raw, 3)
    cols   = ['item', 'unit', 'group'] + months
    df     = _read_data(path, skiprows=2, cols=cols)
    if not df.empty:
        df = df[df['item'].notna() & df['unit'].notna()]
        df = df[df['item'].str.strip().ne('') & df['unit'].str.strip().ne('')]
        for m in months:
            df[m] = _num(df[m])
    return df.reset_index(drop=True), months

def parse_rev_customer(path):
    raw    = pd.read_csv(path, header=None, dtype=str, encoding='utf-8-sig')
    months = _months(raw, 2)
    cols   = ['contract_id', 'name'] + months
    df     = _read_data(path, skiprows=2, cols=cols)
    if not df.empty:
        df = df[df['contract_id'].notna() & df['contract_id'].str.strip().ne('')]
        for m in months:
            df[m] = _num(df[m])
    return df.reset_index(drop=True), months

def parse_quantities(path):
    raw    = pd.read_csv(path, header=None, dtype=str, encoding='utf-8-sig')
    months = _months(raw, 3)
    cols   = ['item', 'unit', 'group'] + months
    df     = _read_data(path, skiprows=2, cols=cols)
    if not df.empty:
        df = df[df['item'].notna() & df['unit'].notna()]
        df = df[df['item'].str.strip().ne('') & df['unit'].str.strip().ne('')]
        for m in months:
            df[m] = _num(df[m])
    return df.reset_index(drop=True), months


# ── Aggregations ───────────────────────────────────────────────────────────────

def aggregate(rp, rp_m, rc, rc_m, qs, qs_m):
    months = rp_m or rc_m or qs_m

    monthly_rev = [
        float(rp[m].sum()) if (not rp.empty and m in rp.columns) else 0.0
        for m in months
    ]

    rev_by_group = {}
    if not rp.empty:
        for grp, g in rp.groupby('group'):
            rev_by_group[str(grp)] = [
                float(g[m].sum()) if m in g.columns else 0.0
                for m in months
            ]

    items = []
    if not rp.empty:
        for _, row in rp.iterrows():
            vals = [float(row.get(m, 0)) for m in months if m in rp.columns]
            items.append({
                'item':    str(row['item']),
                'unit':    str(row['unit']),
                'group':   str(row['group']),
                'monthly': vals,
                'total':   sum(vals),
            })
        items.sort(key=lambda x: x['total'], reverse=True)

    customers = []
    if not rc.empty:
        for _, row in rc.iterrows():
            vals = [float(row.get(m, 0)) for m in rc_m if m in rc.columns]
            customers.append({
                'id':      str(row['contract_id']),
                'name':    str(row['name']),
                'monthly': vals,
                'total':   sum(vals),
            })
        customers.sort(key=lambda x: x['total'], reverse=True)

    monthly_qty = [
        float(qs[m].sum()) if (not qs.empty and m in qs.columns) else 0.0
        for m in months
    ]

    last_rev  = monthly_rev[-1]  if monthly_rev else 0.0
    prev_rev  = monthly_rev[-2]  if len(monthly_rev) >= 2 else 0.0
    mom       = round((last_rev - prev_rev) / prev_rev * 100, 1) if prev_rev else None

    return {
        'months':            months,
        'monthly_revenue':   monthly_rev,
        'revenue_by_group':  rev_by_group,
        'items':             items,
        'customers':         customers,
        'cust_months':       rc_m,
        'monthly_quantities': monthly_qty,
        'kpis': {
            'total_revenue':    sum(monthly_rev),
            'latest_month':     months[-1] if months else None,
            'latest_revenue':   last_rev,
            'mom_growth':       mom,
            'active_contracts': len(rc),
            'total_units':      sum(monthly_qty),
        },
    }


# ── HTML Template ──────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
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
/* Header */
.hdr{padding:20px 32px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.hdr h1{font-size:20px;font-weight:700}.hdr h1 span{color:var(--amber)}
.hdr .meta{font-size:12px;color:var(--muted)}
/* Layout */
.main{padding:24px 32px}
/* KPI Row */
.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 20px}
.kpi .lbl{font-size:10px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.kpi .val{font-size:24px;font-weight:700;line-height:1;margin-bottom:4px}
.kpi .sub{font-size:12px;color:var(--muted)}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:600;margin-top:6px}
.badge.pos{background:rgba(0,200,150,.15);color:var(--green)}
.badge.neg{background:rgba(255,75,107,.15);color:var(--red)}
/* Chart cards */
.ch-full{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:24px}
.ch-2col{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}
.ch-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px}
.ch-title{font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);margin-bottom:14px}
.cw-tall{position:relative;height:280px}
.cw-med{position:relative;height:220px}
/* Tables */
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
@media(max-width:1100px){.kpi-row{grid-template-columns:repeat(3,1fr)}}
@media(max-width:800px){.kpi-row{grid-template-columns:1fr 1fr}.ch-2col{grid-template-columns:1fr}}
</style>
</head>
<body>
<header class="hdr">
  <h1>MK8s <span>Financial Dashboard</span></h1>
  <div class="meta" id="meta-range"></div>
</header>
<main class="main">
  <div class="kpi-row">
    <div class="kpi"><div class="lbl">Total Revenue</div><div class="val" id="k-total">—</div><div class="sub" id="k-range">—</div></div>
    <div class="kpi"><div class="lbl">Latest Month</div><div class="val" id="k-latest">—</div><div class="sub" id="k-month">—</div></div>
    <div class="kpi"><div class="lbl">MoM Growth</div><div class="val" id="k-mom">—</div><div id="k-mom-badge"></div></div>
    <div class="kpi"><div class="lbl">Active Contracts</div><div class="val" id="k-contracts">—</div><div class="sub">unique customers</div></div>
    <div class="kpi"><div class="lbl">Units Sold</div><div class="val" id="k-units">—</div><div class="sub">all products</div></div>
  </div>

  <div class="ch-full">
    <div class="ch-title">Monthly Revenue Trend</div>
    <div class="cw-tall"><canvas id="c-trend"></canvas></div>
  </div>

  <div class="ch-2col">
    <div class="ch-box">
      <div class="ch-title">Revenue by Product Group</div>
      <div class="cw-tall" id="wrap-groups"><canvas id="c-groups"></canvas></div>
    </div>
    <div class="ch-box">
      <div class="ch-title">Top 10 Customers by Revenue</div>
      <div class="cw-tall" id="wrap-topcust"><canvas id="c-topcust"></canvas></div>
    </div>
  </div>

  <div class="ch-full">
    <div class="ch-title">Units Sold by Month</div>
    <div class="cw-med"><canvas id="c-qty"></canvas></div>
  </div>

  <div class="tbl-card">
    <h3>Product Revenue Breakdown</h3>
    <div id="prod-tbl"></div>
  </div>

  <div class="tbl-card">
    <h3>Customer Revenue Detail</h3>
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

const P = ['#003D8F','#FFAA00','#00C896','#FF6B6B','#9B59B6',
           '#00B4D8','#F28C28','#2ECC71','#E74C3C','#1ABC9C','#3498DB'];

const GX = {ticks:{color:'#8899B4',font:{size:11}},grid:{color:'rgba(30,45,74,.6)'}};
const GY = {ticks:{color:'#8899B4',font:{size:11}},grid:{color:'rgba(30,45,74,.6)'}};
const GL = {labels:{color:'#8899B4',font:{size:12},boxWidth:12}};

function emptyHTML(msg){
  return '<div class="empty"><div class="ico">\\u{1F4CA}</div><p>'+msg+'</p></div>';
}

// ── KPIs ──────────────────────────────────────────────────────────────────────
function initKPIs(){
  const k=D.kpis, m=D.months;
  const range = m.length ? m[0]+' \u2013 '+m[m.length-1] : '\u2014';
  document.getElementById('meta-range').textContent = range;
  document.getElementById('k-total').textContent    = eur(k.total_revenue);
  document.getElementById('k-range').textContent    = range;
  document.getElementById('k-latest').textContent   = eur(k.latest_revenue);
  document.getElementById('k-month').textContent    = k.latest_month || '\u2014';
  document.getElementById('k-contracts').textContent= n(k.active_contracts);
  document.getElementById('k-units').textContent    = n(k.total_units);
  if(k.mom_growth !== null && k.mom_growth !== undefined){
    document.getElementById('k-mom').textContent = pct(k.mom_growth);
    const pos = k.mom_growth >= 0;
    document.getElementById('k-mom-badge').innerHTML =
      '<span class="badge '+(pos?'pos':'neg')+'">'+(pos?'\u25b2':'\u25bc')+' vs prev month</span>';
  } else {
    document.getElementById('k-mom').textContent = '\u2014';
  }
}

// ── Revenue Trend ──────────────────────────────────────────────────────────────
function initTrend(){
  new Chart(document.getElementById('c-trend'),{
    type:'line',
    data:{
      labels:D.months,
      datasets:[{
        label:'\u20ac Revenue',data:D.monthly_revenue,
        borderColor:'#003D8F',backgroundColor:'rgba(0,61,143,.12)',fill:true,
        tension:.35,pointBackgroundColor:'#FFAA00',pointRadius:4,pointHoverRadius:6,borderWidth:2
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:GL,tooltip:{callbacks:{label:c=>' '+eur(c.parsed.y)}}},
      scales:{
        x:GX,
        y:{ticks:{color:'#8899B4',font:{size:11},callback:v=>eur(v)},grid:{color:'rgba(30,45,74,.6)'}}
      }
    }
  });
}

// ── Revenue by Product Group (stacked bar) ────────────────────────────────────
function initGroups(){
  const wrap=document.getElementById('wrap-groups');
  const grps=Object.keys(D.revenue_by_group);
  if(!grps.length){wrap.innerHTML=emptyHTML('No product group data');return;}
  new Chart(document.getElementById('c-groups'),{
    type:'bar',
    data:{
      labels:D.months,
      datasets:grps.map((g,i)=>({
        label:g,data:D.revenue_by_group[g],
        backgroundColor:P[i%P.length],borderRadius:2
      }))
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:GL,tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+eur(c.parsed.y)}}},
      scales:{
        x:{ticks:{color:'#8899B4',font:{size:11}},grid:{color:'rgba(30,45,74,.6)'},stacked:true},
        y:{ticks:{color:'#8899B4',font:{size:11},callback:v=>eur(v)},grid:{color:'rgba(30,45,74,.6)'},stacked:true}
      }
    }
  });
}

// ── Top 10 Customers (horizontal bar) ────────────────────────────────────────
function initTopCust(){
  const wrap=document.getElementById('wrap-topcust');
  const top=D.customers.slice(0,10);
  if(!top.length){wrap.innerHTML=emptyHTML('No customer data');return;}
  new Chart(document.getElementById('c-topcust'),{
    type:'bar',
    data:{
      labels:top.map(c=>c.name.length>22?c.name.slice(0,22)+'\u2026':c.name),
      datasets:[{
        label:'Total Revenue',
        data:top.map(c=>c.total),
        backgroundColor:top.map((_,i)=>'rgba(255,170,0,'+Math.max(.2,1-i*.08)+')'),
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

// ── Units Sold (line) ─────────────────────────────────────────────────────────
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

// ── Product Table ─────────────────────────────────────────────────────────────
function initProdTable(){
  const el=document.getElementById('prod-tbl');
  if(!D.items.length){el.innerHTML=emptyHTML('No product data \u2014 add rows to the CSV and re-run');return;}
  const m=D.months, show=m.slice(-3);
  let h='<div class="ovx"><table class="dt"><thead><tr><th>Item</th><th>Unit</th><th>Group</th>';
  show.forEach(x=>h+='<th class="r">'+x+'</th>');
  h+='<th class="r">Total</th></tr></thead><tbody>';
  D.items.forEach(item=>{
    const vals=show.map(x=>{const i=m.indexOf(x);return i>=0?(item.monthly[i]||0):0;});
    h+='<tr><td>'+esc(item.item)+'</td><td class="m">'+esc(item.unit)+'</td>';
    h+='<td><span class="pill">'+esc(item.group)+'</span></td>';
    vals.forEach(v=>h+='<td class="r">'+eur(v)+'</td>');
    h+='<td class="r">'+eur(item.total)+'</td></tr>';
  });
  el.innerHTML=h+'</tbody></table></div>';
}

// ── Customer Table ────────────────────────────────────────────────────────────
let _custs=[];
function initCustTable(){_custs=D.customers;renderCusts(_custs);}

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
    h+='<td class="r">'+eur(c.total)+'</td></tr>';
  });
  el.innerHTML=h+'</tbody></table></div>';
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  initKPIs();
  if(D.months.length){
    initTrend();
    initGroups();
    initTopCust();
    initQty();
  }
  initProdTable();
  initCustTable();
});
</script>
</body>
</html>"""


def generate_html(data):
    return HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))


# ── File detection ─────────────────────────────────────────────────────────────

def _classify(path: Path):
    """Return the role of a CSV based on its filename keywords."""
    name = path.name.lower()
    if 'customer' in name:
        return 'revenue_customer'
    if 'quantit' in name:
        return 'quantities'
    return 'revenue_product'

def resolve_files(inputs: list[str]) -> dict:
    """
    Accept either:
      • a single directory  → find all *mk8s*.csv files and classify them
      • 1–3 explicit file paths → classify each by filename keywords
    Returns dict with keys: revenue_product, revenue_customer, quantities.
    """
    if not inputs:
        inputs = ['.']

    # Single directory
    if len(inputs) == 1 and Path(inputs[0]).is_dir():
        directory = Path(inputs[0]).resolve()
        candidates = sorted(directory.glob('*.csv'))
        mk8s = [f for f in candidates if 'mk8s' in f.name.lower()]
        if not mk8s:
            # Fall back to all CSVs if none match 'mk8s'
            mk8s = candidates
        found = {}
        for f in mk8s:
            role = _classify(f)
            if role not in found:
                found[role] = f
            else:
                print(f"  WARNING: multiple files match role '{role}', using: {found[role].name}")
        return found

    # Explicit file paths
    found = {}
    for raw in inputs:
        p = Path(raw).resolve()
        if not p.exists():
            sys.exit(f"ERROR: file not found: {p}")
        role = _classify(p)
        if role in found:
            sys.exit(f"ERROR: two files classified as '{role}':\n  {found[role]}\n  {p}")
        found[role] = p
    return found


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description='Generate MK8s financial dashboard from CSV exports.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # auto-detect mk8s CSVs in a directory
  python generate_dashboard.py /path/to/exports/

  # pass files explicitly (order doesn't matter — classified by filename)
  python generate_dashboard.py revenue.csv customers.csv quantities.csv

  # current directory, custom output name
  python generate_dashboard.py --output report.html
        """,
    )
    ap.add_argument('paths', nargs='*', metavar='PATH',
                    help='Directory containing mk8s CSVs, or up to 3 explicit CSV file paths')
    ap.add_argument('--output', default=DEFAULT_OUTPUT,
                    help=f'Output HTML file (default: {DEFAULT_OUTPUT})')
    args = ap.parse_args()

    files = resolve_files(args.paths)

    required = {'revenue_product', 'revenue_customer', 'quantities'}
    missing  = required - files.keys()
    if missing:
        labels = {
            'revenue_product':  'Revenue Projection (products)',
            'revenue_customer': 'Revenue Projection (customers)',
            'quantities':       'Quantities Sold',
        }
        print("ERROR: could not find files for:")
        for role in missing:
            print(f"  • {labels[role]}  (filename should contain 'customer' or 'quantit')")
        sys.exit(1)

    # Output path sits next to the revenue_product file by default
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = files['revenue_product'].parent / out_path

    print("Files resolved:")
    for role, p in files.items():
        print(f"  {role:<20} {p.name}")

    rp, rp_m = parse_rev_product(files['revenue_product'])
    rc, rc_m = parse_rev_customer(files['revenue_customer'])
    qs, qs_m = parse_quantities(files['quantities'])
    print(f"\nRows — Products: {len(rp)} | Customers: {len(rc)} | Quantities: {len(qs)}")

    data = aggregate(rp, rp_m, rc, rc_m, qs, qs_m)
    out_path.write_text(generate_html(data), encoding='utf-8')
    print(f"\nDashboard saved to: {out_path}")
    print(f'Open with:  open "{out_path}"')


if __name__ == '__main__':
    main()
