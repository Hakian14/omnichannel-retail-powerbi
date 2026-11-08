"""
Aggregate the star schema into compact JSON for the web dashboard (docs/index.html).

    python scripts/build_dashboard_data.py     -> docs/data/*.json

The browser cannot hold 548k sales lines, so the facts are pre-aggregated to the grains the
dashboard measures need. Every measure in the dashboard is computed in JavaScript from these
files using the same definitions as model/measures.dax (see docs/index.html, section "measures").
"""

from __future__ import annotations

import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "star_schema")
OUT = os.path.join(ROOT, "docs", "data")


def ym(date_key: pd.Series) -> pd.Series:
    return (date_key // 100).astype(str).str.replace(r"(\d{4})(\d{2})", r"\1-\2", regex=True)


def dump(name: str, df: pd.DataFrame):
    path = os.path.join(OUT, f"{name}.json")
    payload = {"columns": list(df.columns), "rows": df.to_numpy().tolist()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"), default=lambda v: v.item() if hasattr(v, "item") else v)
    print(f"  {name:12s} {len(df):>7,} rows  {os.path.getsize(path) / 1024:7.0f} KB")


def main():
    os.makedirs(OUT, exist_ok=True)
    sales = pd.read_csv(os.path.join(D, "fact_sales.csv.gz"))
    stores = pd.read_csv(os.path.join(D, "dim_store.csv"))
    products = pd.read_csv(os.path.join(D, "dim_product.csv"))
    customers = pd.read_csv(os.path.join(D, "dim_customer.csv"))
    targets = pd.read_csv(os.path.join(D, "fact_targets.csv"))
    footfall = pd.read_csv(os.path.join(D, "fact_footfall.csv"))
    inventory = pd.read_csv(os.path.join(D, "fact_inventory.csv.gz"))

    s = sales.merge(products[["product_key", "category", "subcategory", "season", "sku"]], on="product_key")
    s = s.merge(customers[["customer_key", "loyalty_tier"]], on="customer_key", how="left")
    s["ym"] = ym(s["date_key"])
    s["year"] = s["date_key"] // 10000

    # 1. sales by month x store x category x subcategory x season
    s["gross"] = s["unit_price"] * s["quantity"]
    agg = s.groupby(["ym", "store_key", "category", "subcategory", "season"], as_index=False).agg(
        net=("net_sales", "sum"), cost=("cost_amount", "sum"), units=("quantity", "sum"), gross=("gross", "sum"))
    dump("sales", agg)

    # 2. transactions by month x store (distinct count is not additive across categories)
    tx = s.groupby(["ym", "store_key"]).agg(
        transactions=("transaction_id", "nunique"),
        identified_net=("net_sales", lambda x: x[s.loc[x.index, "customer_key"] > 0].sum()),
        loyalty_net=("net_sales", lambda x: x[s.loc[x.index, "loyalty_tier"].isin(["Silver", "Gold"])].sum()),
    ).reset_index()
    dump("transactions", tx)

    # 3. daily sales by store (for the Tet / sale-day view)
    daily = s.groupby(["date_key", "store_key"], as_index=False).agg(net=("net_sales", "sum"), transactions=("transaction_id", "nunique"))
    daily["date"] = pd.to_datetime(daily["date_key"].astype(str)).dt.strftime("%Y-%m-%d")
    dump("daily", daily[["date", "store_key", "net", "transactions"]])

    # 4. targets and footfall by month x store
    dump("targets", targets.rename(columns={"year_month": "ym"}))
    ff = footfall.assign(ym=ym(footfall["date_key"])).groupby(["ym", "store_key"], as_index=False)["footfall"].sum()
    dump("footfall", ff)

    # 5. month-end inventory by store x season x subcategory
    inv = inventory.merge(products[["product_key", "season", "subcategory", "category"]], on="product_key")
    inv["ym"] = ym(inv["date_key"])
    inv_agg = inv.groupby(["ym", "store_key", "category", "subcategory", "season"], as_index=False).agg(
        soh=("stock_on_hand", "sum"), value=("stock_value_at_cost", "sum"))
    dump("inventory", inv_agg)

    # 6. customers: per year x store x tier -> identified customers, repeat customers, net
    ident = s[s["customer_key"] > 0]
    per_cust = ident.groupby(["year", "store_key", "loyalty_tier", "customer_key"]).agg(
        txns=("transaction_id", "nunique"), net=("net_sales", "sum")).reset_index()
    cust = per_cust.groupby(["year", "store_key", "loyalty_tier"], as_index=False).agg(
        customers=("customer_key", "nunique"), repeat_customers=("txns", lambda x: int((x >= 2).sum())), net=("net", "sum"))
    dump("customers", cust)
    per_cust_total = ident.groupby(["year", "loyalty_tier", "customer_key"]).agg(txns=("transaction_id", "nunique"), net=("net_sales", "sum")).reset_index()
    dump("customers_total", per_cust_total.groupby(["year", "loyalty_tier"], as_index=False).agg(
        customers=("customer_key", "nunique"), repeat_customers=("txns", lambda x: int((x >= 2).sum())), net=("net", "sum")))
    # age-band mix per year (not store-specific; the page shows it unfiltered by store)
    age = ident.merge(customers[["customer_key", "age_band", "gender"]], on="customer_key")
    age_mix = age.groupby(["year", "age_band", "gender"], as_index=False).agg(net=("net_sales", "sum"), customers=("customer_key", "nunique"))
    dump("age_mix", age_mix)
    joins = customers[customers["customer_key"] > 0].assign(ym=lambda d: d["join_date"].str[:7]).groupby("ym", as_index=False).size().rename(columns={"size": "new_members"})
    dump("members", joins[joins["ym"] >= "2024-01"])

    # 7. SKU performance per year (store channel split not needed)
    sku = s.groupby(["year", "sku", "category", "subcategory", "season", "product_key"], as_index=False).agg(
        units=("quantity", "sum"), net=("net_sales", "sum"), cost=("cost_amount", "sum"))
    last_snap = inv[inv["date_key"].isin([20241231, 20251231])].assign(year=lambda d: d["date_key"] // 10000)
    stock = last_snap.groupby(["year", "product_key"], as_index=False)["stock_on_hand"].sum().rename(columns={"stock_on_hand": "soh_year_end"})
    sku = sku.merge(stock, on=["year", "product_key"], how="left").fillna({"soh_year_end": 0}).drop(columns="product_key")
    dump("skus", sku)

    # 8. dimensions
    dump("stores", stores)
    months = sorted(s["ym"].unique())
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump({"months": months, "years": sorted(int(y) for y in s["year"].unique()),
                   "categories": sorted(s["category"].unique()), "subcategories": sorted(s["subcategory"].unique()),
                   "snapshot_date": pd.to_datetime(str(sales["date_key"].max())).strftime("%d %b %Y"),
                   "total_rows": int(len(sales))}, f)
    print("  meta.json")


if __name__ == "__main__":
    main()
