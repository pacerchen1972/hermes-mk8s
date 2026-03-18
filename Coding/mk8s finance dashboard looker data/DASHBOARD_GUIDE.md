# MK8s Financial Dashboard — Analyst Edition

## Overview

A comprehensive financial analysis dashboard for MK8s Managed Kubernetes revenue data with **powerful configuration options** for data analysts to:
- Filter by date range, aggregation level, and comparison periods
- Group data by SKU, customer, or product group
- Apply threshold and top N filters
- Toggle KPI visibility and customize metrics
- Configure chart types and normalization
- Export filtered data to CSV/JSON

**File**: `mk8s-analyst-dashboard.html` (125.5 KB, self-contained)

---

## Quick Start

1. **Open** the dashboard in a web browser: `open mk8s-analyst-dashboard.html`
2. **Configure** using the tabs at the top (Period → Data → KPIs → Charts → Visual → Export)
3. **All charts and tables update instantly** based on your selections
4. **Export** filtered data with one click

---

## Configuration Tabs

### 📅 **Period Tab**
Configure the time range and aggregation level:

- **Start Month / End Month**: Choose any 12-month span (Apr 2025 – Mar 2026)
- **Aggregation**:
  - Monthly (default) — show all months individually
  - Quarterly — group into 4 quarters (Q1, Q2, Q3, Q4)
  - Annual — single year total
- **Comparison Mode**:
  - None (default) — show selected period only
  - vs Previous Period — compare with prior months
  - vs Year-over-Year — compare with same months 12 months ago
- **Apply Period Filter** — executes the date range change
- **Reset to All** — returns to full 12-month view

**Example**: Select Apr 2025 – Sep 2025, aggregation = Quarterly, comparison = vs Previous Period to see Q-over-Q growth in H1 2025.

---

### 📊 **Data Tab**
Control how data is grouped and filtered:

- **Group By**:
  - SKU (default) — revenue breakdown by product (10 items)
  - Customer — revenue by customer (500 items)
  - Product Group — aggregate SKUs by group (1 group: Managed Kubernetes)

- **Top N Items**:
  - All (default) — show all items in selection
  - Top 5, Top 10, Top 20, Top 50 — limit to top N by total revenue
  - Useful for focusing on key drivers (top 10 customers generate ~80% of revenue)

- **Min Revenue (€)** (0 – €100,000 slider):
  - Filter out items below a threshold
  - Example: Set to €10,000 to see only "significant" revenue lines

- **Customer Status** (Active | Churned | New):
  - **Active**: Customers with revenue in last 3 months
  - **Churned**: Customers with past revenue but none in last 3 months
  - **New**: Customers with first revenue recently
  - Multi-select: choose which cohorts to include

**Example**: Group by Customer, Top 20, threshold €5,000, active only = top 20 active customers generating >€5k/period.

---

### 📈 **KPIs Tab**
Choose which key performance indicators to display:

- **Visible KPIs** (checkboxes):
  - Total Revenue — 12-month (or filtered period) aggregate
  - Latest Month — most recent month in selection
  - MoM Growth % — month-over-month growth rate
  - Active Contracts — customers with recent revenue
  - Churned Contracts — lost customers
  - Revenue/Customer — average revenue per active customer

- **Metric Precision**:
  - 0 decimals — round to nearest €1
  - 1 decimal — show €X.X
  - 2 decimals (default) — show €X.XX

**Example**: Uncheck "Churned" and "MoM Growth" if you're analyzing customer concentration (toggle Total, Latest, Active, Revenue/Customer).

---

### 📉 **Charts Tab**
Customize chart appearance and data representation:

- **Revenue Chart Type**: Line | Bar | Area
  - Line: trends over time (default for trend charts)
  - Bar: compare discrete periods
  - Area: emphasize cumulative contribution

- **SKU Chart Type**: Line (Stacked) | Bar (Stacked) | Area (Stacked)
  - Stacked formats show total + composition
  - Use Area for smooth trends, Bar for period comparisons

- **Normalization**:
  - Actual Values (default) — show €revenue amounts
  - % of Total — show each SKU as % of total revenue per month
  - Useful for tracking mix shift (e.g., Savings Plan growth from 0% to 5%)

**Example**: Change SKU to "Bar (Stacked)" with "% of Total" to see how product mix is evolving (vCPU/Savings Plan share is growing vs. Dedicated Core).

---

### ⚙️ **Visual Tab**
Display and theme preferences:

- **Currency Display**:
  - € (Symbol) — €3,586,444 (compact, space-saving)
  - EUR (Code) — 3,586,444 EUR
  - Euro (Name) — 3,586,444 Euro

- **Theme**: Dark | Light
  - Dark (default) — IONOS-adjacent dark theme, easier on eyes
  - Light — high-contrast light theme

---

### 💾 **Export Tab**
Download filtered data:

- **CSV Export**: Spreadsheet-compatible format
  - Includes all rows/columns based on current filters
  - Opens in Excel, Google Sheets, etc.
- **JSON Export**: Raw data for programmatic analysis
  - Includes full structure with metadata
  - Ideal for further processing or API integration

---

## Key Features

### Dynamic Tables
- **Product Table**: Shows all filtered SKUs with selected months, totals, and growth %
  - Columns auto-adjust to date range (e.g., only show filtered 6 months, not all 12)
  - Sorted by total revenue (highest first)
  - Includes **Growth %** column (% change from first to last month in selection)

- **Customer Table**: Shows filtered customers with search
  - Searchable by company name or contract ID
  - Shows selected months + annual total
  - Updated in real-time as you change filters
  - Searchable even while filters are applied
  - **Export Table** button for selected results only

### Smart KPI Cards
- KPI cards update based on **selected period**, not always 12 months
- Example: Select Apr–Jun 2025 → "Total Revenue" shows Q2 2025 total
- "Latest Month" always shows most recent month in selection
- "Active Contracts" recalculates for new period (e.g., if selecting Q1 only, active = customers with Q1 revenue)

### Responsive Layout
- On desktop: 6-column KPI row, side-by-side 2-column charts
- On tablet: 3-column KPI row, single-column charts
- On mobile: 2-column KPI row, stacked configuration panel

### Data Completeness Badge
- Shows "⚠️ March 2026 partial" warning if latest month is incomplete
- Reminds analysts that growth rates may be skewed in Mar 2026 (only ~30 days of data)

---

## Common Workflows

### 1. **Executive Summary for Q1 2026**
```
Period: Jan 2026 – Mar 2026, Aggregation = Quarterly
Data: Group by SKU, All items
KPIs: Total, Latest, MoM, Active, RPC
→ Shows Q1 revenue breakdown by product + growth rate
```

### 2. **Top Customer Analysis**
```
Period: All (Apr 2025 – Mar 2026)
Data: Group by Customer, Top 20, threshold €5,000, Active only
KPIs: All visible
Charts: Revenue Concentration donut shows Top 20 = 70% of total
→ Identifies key accounts for retention focus
```

### 3. **Savings Plan Adoption Trend**
```
Period: Oct 2025 – Mar 2026 (when Savings Plan started)
Data: Group by SKU, All
Charts: Trend = Line, Charts area = Area (% of Total)
→ Visualizes SPKC/SPKR growth from 0% to 5% of mix
```

### 4. **Product Mix Shift**
```
Period: Apr 2025 – Mar 2026
Data: Group by SKU, Top 5
Charts: Stacked Area with % normalization
→ Shows how dominant SKUs change over time (Dedicated Core declining, vCPU/Savings growing)
```

### 5. **Churned Customer Investigation**
```
Period: All
Data: Group by Customer, Top 50, Customer Status = Churned only
KPIs: Hide "Active", show all others
Table: Sort by most recent revenue date
→ Identifies customers lost in specific months
```

---

## Data Source & Refresh

**Data embedded in HTML**: All 500 customers, 10 SKUs, 12 months (Apr 2025 – Mar 2026)

**To regenerate with fresh CSV data**:
```bash
python3 generate_dashboard_v2.py . --output mk8s-financial-dashboard.html
# Then embed new data into analyst dashboard:
python3 << 'EOF'
import json, re
with open('mk8s-financial-dashboard.html') as f:
    match = re.search(r'const D = ({.*?});', f.read())
    if match:
        with open('mk8s-analyst-dashboard.html') as tf:
            output = tf.read().replace('__DATA__', match.group(1))
        with open('mk8s-analyst-dashboard.html', 'w') as tf:
            tf.write(output)
EOF
```

---

## State Persistence

- **LocalStorage**: Configuration choices (period, data filters, KPI visibility) are saved automatically
- **URL Sync** (optional): Share filter state via URL parameters (future enhancement)
- **Browser reload**: Settings persist across page refreshes in same browser

---

## Technical Notes

### Data Pipeline Execution Order
1. **Period Filter**: Extract months within selected range
2. **Grouping**: Aggregate by SKU/Customer/Group
3. **Aggregation**: Collapse to quarterly/annual if selected
4. **Top N Sort**: Sort by revenue, keep top N
5. **Threshold Filter**: Remove items < €X
6. **Output**: FilteredDataset used for all charts/tables

### Chart Instances
- Charts stored in `chartInstances` object
- Destroyed & recreated on each filter change for accurate updates
- Memory-efficient for datasets up to 1000 items

### Column Generation
- Table columns **dynamically generated** based on selected date range
- Example: Select 6 months → table shows 6 month columns, not 12
- Last 3 months + total always shown; others omitted if space-constrained

---

## Keyboard Shortcuts (Future)
- `Ctrl+E`: Export CSV
- `Ctrl+L`: Reset to all data
- `Ctrl+/`: Help panel

---

## Support & Customization

For custom KPIs, derived metrics, or additional visualizations, contact the data engineering team with your use case.

**Last Updated**: March 2026
**Data Completeness**: 100% through Feb 2026, ~30% for Mar 2026
