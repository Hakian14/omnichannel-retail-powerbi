# Build guide — from CSVs to the finished report

> **Shortcut:** `powerbi/OmnichannelRetail.pbip` already contains steps 1–4 below as a Power BI
> Project. Open it, set the `DataFolder` parameter, refresh, and jump to step 5 (see
> [`powerbi/README.md`](../powerbi/README.md)). The manual steps remain here for learning or as a fallback.

Estimated time: 60–90 minutes in Power BI Desktop manually; ~10 minutes with the project file. Nothing here needs a Pro licence.

## 0. Prerequisites

- Power BI Desktop (any 2024+ release).
- This repository cloned locally; note the absolute path to `data/star_schema/`.
- Optional: run `python data/generate_data.py` if you want to regenerate the CSVs.

## 1. Model settings first

`File → Options and settings → Options → Current file → Data Load`

- **Untick "Auto date/time"** — the model has its own `dim_date`.
- Untick "Autodetect new relationships after data is loaded" — relationships are created deliberately in step 3.

## 2. Load the data with Power Query

1. `Home → Transform data` to open Power Query.
2. `Manage Parameters → New Parameter`: name `DataFolder`, type Text, value = your path to `data/star_schema/` **with a trailing backslash**.
3. For each block in [`model/power_query.pq`](../model/power_query.pq): `New Source → Blank Query → Advanced Editor`, paste, rename the query to the name in the comment header. Create `fnLoadCsv` first; the others depend on it.
4. Right-click `fnLoadCsv` and `dim_month` → keep them enabled; right-click `_Measures` → leave load enabled (it hosts measures).
5. `Close & Apply`. Expect ~10 s for `fact_sales` (548k rows).

## 3. Relationships

In Model view create these **single-direction, one-to-many** relationships (dimension side = 1):

| From (1) | To (*) |
|---|---|
| `dim_date[date_key]` | `fact_sales[date_key]` |
| `dim_date[date_key]` | `fact_inventory[date_key]` |
| `dim_date[date_key]` | `fact_footfall[date_key]` |
| `dim_store[store_key]` | `fact_sales[store_key]` |
| `dim_store[store_key]` | `fact_inventory[store_key]` |
| `dim_store[store_key]` | `fact_footfall[store_key]` |
| `dim_store[store_key]` | `fact_targets[store_key]` |
| `dim_product[product_key]` | `fact_sales[product_key]` |
| `dim_product[product_key]` | `fact_inventory[product_key]` |
| `dim_customer[customer_key]` | `fact_sales[customer_key]` |
| `dim_month[year_month]` | `dim_date[year_month]` |
| `dim_month[year_month]` | `fact_targets[year_month]` |

Then:

- Select `dim_date` → `Table tools → Mark as date table` → column `date`.
- Hide every key column on the fact tables, hide `_Measures[_]`, and hide the fact tables' `year_month`/`date_key` columns from report view so authors only pick fields from dimensions.
- Set `dim_date[month_name]` → *Sort by column* `month_number`; `dim_date[day_name]` → sort by `day_of_week`.

## 4. Measures

1. Select the `_Measures` table.
2. Copy each measure from [`model/measures.dax`](../model/measures.dax) into `New measure`. The file is ordered so that base measures come first.
3. Set display folders to the `// Folder:` names and formats:
   - currency measures → `#,0` (VND has no decimals), or use the `Net Sales Short` label measure for cards;
   - `%` measures → Percentage, 1 decimal;
   - counts → Whole number with thousands separator.
4. Quick check: a card with `[Net Sales]` and a slicer on `dim_date[year] = 2025` must show **118,171,760,000**. `[Target Achievement %]` for 2025 must show **97.8%**.

## 5. Report pages

Apply the theme first: `View → Themes → Browse for themes → report/theme.json`.

Then build the five pages following [`report/report_spec.md`](../report/report_spec.md). Suggested canvas: 1280 × 720, page background from theme. Keep the filter bar identical on every page (copy–paste the slicer group, then `View → Sync slicers`).

`report/preview_executive_overview.png` shows the intended layout of page 1.

## 6. Performance checklist before publishing

- `Performance Analyzer` on page 1: every visual under 500 ms on this dataset.
- `View → Model view → Properties`: no bi-directional relationships.
- `DAX Studio → View Metrics` (optional): `fact_sales[transaction_id]` will be the largest column — that is expected; it is needed for `DISTINCTCOUNT`. If model size matters, replace it with an integer transaction key in Power Query.
- Remove unused columns: `dim_date[holiday_name]` if you do not use it in tooltips, `dim_customer[customer_id]`.

## 7. Publish and schedule

- `Home → Publish` to a workspace; set the `DataFolder` parameter on the dataset's settings page if the gateway path differs.
- For a production version, point `fnLoadCsv` at a SQL view instead of CSVs — the star schema maps 1:1 to a warehouse layer.

## 8. Commit your work

```
report/omnichannel_retail.pbix        <- the finished file
report/screenshots/01_executive.png   <- one screenshot per page
```

Power BI Desktop can also save as a **Power BI Project (.pbip)**, which stores the model as text (TMDL) and the report as JSON — much friendlier for Git diffs. If you use it, commit the whole `.pbip` folder instead of the `.pbix`.
