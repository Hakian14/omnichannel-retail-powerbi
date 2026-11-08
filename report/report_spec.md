# Report specification

Five pages, each built for one audience and one decision. Every visual lists the measures it
uses (all defined in [`model/measures.dax`](../model/measures.dax)) so the report can be
rebuilt exactly, or reviewed by someone who does not have Power BI.

Global: a thin **filter bar** at the top of every page with slicers for `dim_date[year_month]`
(between-style date range), `dim_store[region]`, `dim_store[channel]`, and a sync'd
`dim_product[category]`. Page background `#f9f9f7`; visuals on white cards with a 6 px radius
(see [`theme.json`](theme.json)). Dynamic page title uses `[Selected Period Label]`.

---

## Page 1 — Executive Overview

*Audience:* leadership, weekly. *Decision:* are we on plan, and where is the gap coming from?

| Zone | Visual | Fields / measures | Notes |
|---|---|---|---|
| KPI row (5 cards) | Card × 5 | `[Net Sales]` with `[Net Sales YoY %]` as sub-label; `[Gross Margin %]`; `[Target Achievement %]`; `[Online Share %]`; `[Same-Store Sales Growth %]` | Target card uses `[Target Status]` for green/red conditional colour. |
| Trend | Line chart | X `dim_date[year_month]`, Y `[Net Sales]`, `[Net Sales LY]` | Two series max; LY as thinner grey line. Tooltip shows `[Net Sales YoY %]`. |
| Target bridge | Clustered bar | X `dim_store[region]`, Y `[Net Sales]`, `[Sales Target]` | Sorted by `[Variance to Target]`. |
| Channel mix | 100% stacked bar (single bar per year) | Legend `dim_store[channel]`, Y `[Net Sales]` | Shows online share drifting; sorted fixed by legend order, not value. |
| Category mix | Clustered bar | X `dim_product[category]`, Y `[Net Sales]`, `[Net Sales LY]` | |
| Footer | Text | `[Last Refresh Label]` | |

Finding this page surfaced on the synthetic data: 2025 closed at **97.8% of target**, and 14 of
15 locations were below plan — targets were set at LY + 8% while comparable-store growth ran at
+5.3%. Either targets were too aggressive for mature stores, or the growth plan assumed new-store
contribution that should have been budgeted separately.

## Page 2 — Channel Performance

*Audience:* e-commerce and retail ops leads. *Decision:* where to shift marketing and stock.

| Visual | Fields / measures |
|---|---|
| Matrix: channel × month | Rows `dim_store[channel]`, Columns `dim_date[year_month]`, Values `[Net Sales]`, `[Net Sales YoY %]` with data bars |
| Small multiples line | `[Net Sales]` by `dim_date[year_month]`, small multiples on `dim_store[channel]` |
| Avg basket by channel | Clustered bar `[Avg Basket Value]`, `[Units per Transaction]` by `dim_store[channel]` |
| Discount dependence | Scatter: X `[Discount Rate %]`, Y `[Gross Margin %]`, size `[Net Sales]`, detail `dim_store[store_name]` |
| Tet window callout | Line of daily `[Net Sales]` for Jan–Feb with `dim_date[is_holiday]` shading | Shows online carrying sales while stores are closed for Tet. |

## Page 3 — Store Performance

*Audience:* regional managers. *Decision:* which stores need attention this month.

| Visual | Fields / measures |
|---|---|
| Store league table | Table: `dim_store[store_name]`, `[Net Sales]`, `[Net Sales YoY %]`, `[Target Achievement %]` (icon set), `[Sales per sqm]`, `[Conversion Rate %]`, `[Avg Basket Value]` — sorted by `[Target Achievement %]` |
| Map | Azure map: `dim_store[city]`, bubble `[Net Sales]`, colour `[Target Achievement %]` |
| Conversion vs footfall | Scatter: X `[Footfall]`, Y `[Conversion Rate %]`, detail store, size `[Net Sales]` |
| Sales per sqm ranking | Bar chart, `dim_store[store_format]` as legend |
| Store detail tooltip page | `[Net Sales]` 13-month sparkline, `[Weeks of Cover]`, `[Sell-Through %]` |

Finding: the two outlets (Bac Ninh, Bien Hoa) have the lowest **sales per sqm (20.5M and
16.4M VND)** and the highest discount rate — outlet productivity is the weakest link in the
estate, not the newest standard store (Vinh, 21.5M).

## Page 4 — Product & Inventory

*Audience:* merchandising / planning. *Decision:* what to mark down, what to re-order.

| Visual | Fields / measures |
|---|---|
| Category → subcategory decomposition tree | `[Net Sales]` by `category` → `subcategory` → `color` |
| Sell-through by subcategory | Bar `[Sell-Through %]` by `dim_product[subcategory]`, legend `season` |
| Weeks of cover trend | Line `[Weeks of Cover]` by `year_month`, legend `dim_product[season]`, constant line at 6 weeks |
| Top / bottom 10 SKUs | Two tables: `sku`, `[Units Sold]`, `[Net Sales]`, `[Gross Margin %]`, `[Weeks of Cover]` |
| Price band mix | Stacked bar `[Net Sales]` by `price_band`, legend `category` |

Finding: **FW stock sat at 14 weeks of cover at end-April 2025** against 6 weeks for SS — a
classic end-of-season overhang. A markdown plan for FW in March, or a smaller FW buy, is worth
roughly the carrying cost of eight weeks of stock across 12 stores.

## Page 5 — Customers & Loyalty

*Audience:* CRM team. *Decision:* where identification and loyalty are working.

| Visual | Fields / measures |
|---|---|
| KPI cards | `[Identified Customers]`, `[Identified Sales Share %]`, `[Loyalty Share %]`, `[Repeat Rate %]`, `[Avg Spend per Identified Customer]` |
| Identification by channel | Bar `[Identified Sales Share %]` by `dim_store[channel]` | Online = 100% by design; stores ~45%. |
| Tier mix | Donut `[Net Sales]` by `dim_customer[loyalty_tier]` (4 slices max) |
| Repeat rate by tier × age band | Matrix with conditional background |
| New members trend | Column: count of `dim_customer` by `join_date` month |

---

## Interactions and UX

- Slicers sync across all five pages; the date range is the only slicer with "select all" allowed.
- Cross-highlight is **off** between the KPI cards and the rest of the page (cards filter, not highlight).
- Each page has a bookmark-driven "Reset filters" button.
- Drill-through from any store bar/table row to **Store detail** (hidden page) with the store's 13-month trend, target variance by month and top 10 SKUs.
- Mobile layout defined for Page 1 only (KPI cards stacked, trend line, target bars).

## Naming conventions

- Tables: `dim_*`, `fact_*`, `_Measures`.
- Measures: Title Case, unit suffix (`%` for ratios), no abbreviations other than LY/YoY/MTD/YTD.
- Display folders: numbered (`1. Sales`, `2. Margin`, …) so they sort in the field list in reading order.
