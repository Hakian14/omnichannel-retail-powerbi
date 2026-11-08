"""
Synthetic omnichannel fashion-retail dataset in star-schema form, ready to
load into Power BI (or any BI tool).

    python data/generate_data.py          # writes CSVs to data/star_schema/

Modelled after a Vietnamese family-fashion chain: 12 physical stores across
three regions plus three online channels (website, mobile app, marketplace),
two full years of daily sales, month-end inventory snapshots, monthly sales
targets per store and daily footfall for physical stores.

Deterministic (fixed seed). No real company data.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

SEED = 7
START = date(2024, 1, 1)
END = date(2025, 12, 31)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "star_schema")

# Tet (Lunar New Year) windows - demand peaks before, stores quiet during
TET = [(date(2024, 2, 5), date(2024, 2, 14)), (date(2025, 1, 25), date(2025, 2, 2))]
HOLIDAYS = {date(2024, 4, 30), date(2024, 5, 1), date(2024, 9, 2), date(2025, 4, 30), date(2025, 5, 1), date(2025, 9, 2)}

STORES = [
    # code, name, channel_type, channel, city, region, format, sqm, open_date
    ("S01", "Hanoi - Cau Giay", "Store", "Physical store", "Ha Noi", "North", "Flagship", 420, date(2019, 3, 15)),
    ("S02", "Hanoi - Long Bien", "Store", "Physical store", "Ha Noi", "North", "Standard", 260, date(2020, 10, 1)),
    ("S03", "Hai Phong - Le Chan", "Store", "Physical store", "Hai Phong", "North", "Standard", 240, date(2021, 6, 12)),
    ("S04", "Hai Duong - City", "Store", "Physical store", "Hai Duong", "North", "Standard", 210, date(2022, 1, 20)),
    ("S05", "Bac Ninh - City", "Store", "Physical store", "Bac Ninh", "North", "Outlet", 180, date(2022, 9, 9)),
    ("S06", "Da Nang - Hai Chau", "Store", "Physical store", "Da Nang", "Central", "Flagship", 380, date(2020, 5, 5)),
    ("S07", "Hue - City", "Store", "Physical store", "Hue", "Central", "Standard", 200, date(2023, 3, 3)),
    ("S08", "Vinh - City", "Store", "Physical store", "Vinh", "Central", "Standard", 190, date(2024, 8, 16)),   # opened mid-window
    ("S09", "HCMC - District 1", "Store", "Physical store", "Ho Chi Minh City", "South", "Flagship", 450, date(2019, 11, 11)),
    ("S10", "HCMC - Thu Duc", "Store", "Physical store", "Ho Chi Minh City", "South", "Standard", 270, date(2021, 2, 2)),
    ("S11", "Can Tho - Ninh Kieu", "Store", "Physical store", "Can Tho", "South", "Standard", 230, date(2022, 4, 18)),
    ("S12", "Bien Hoa - City", "Store", "Physical store", "Bien Hoa", "South", "Outlet", 170, date(2025, 3, 1)),   # opened mid-window
    ("W01", "Website", "Online", "Website", "Online", "Online", "Online", 0, date(2019, 1, 1)),
    ("A01", "Mobile app", "Online", "Mobile app", "Online", "Online", "Online", 0, date(2021, 7, 1)),
    ("M01", "Marketplace", "Online", "Marketplace", "Online", "Online", "Online", 0, date(2020, 3, 1)),
]
# relative sales weight per store (before openings / seasonality)
STORE_WEIGHT = [1.6, 0.9, 0.8, 0.6, 0.5, 1.3, 0.6, 0.5, 1.8, 0.9, 0.7, 0.45, 1.5, 1.2, 1.1]

CATEGORIES = {
    "Women":  [("T-shirt", 199_000), ("Shirt", 349_000), ("Dress", 449_000), ("Jeans", 499_000), ("Jacket", 699_000), ("Shorts", 249_000), ("Knitwear", 399_000)],
    "Men":    [("T-shirt", 199_000), ("Polo", 299_000), ("Shirt", 349_000), ("Jeans", 549_000), ("Jacket", 749_000), ("Shorts", 249_000), ("Chinos", 449_000)],
    "Kids":   [("T-shirt", 149_000), ("Dress", 299_000), ("Jeans", 329_000), ("Jacket", 449_000), ("Shorts", 169_000), ("Pyjamas", 249_000)],
}
CAT_WEIGHT = {"Women": 0.46, "Men": 0.34, "Kids": 0.20}
SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
COLORS = ["Black", "White", "Navy", "Beige", "Olive", "Red", "Grey", "Blue"]
MONTH_SEASON = {1: 1.35, 2: 0.80, 3: 0.90, 4: 1.00, 5: 1.05, 6: 1.10, 7: 1.00, 8: 0.95, 9: 1.00, 10: 1.10, 11: 1.40, 12: 1.30}
DOW = {0: 0.85, 1: 0.85, 2: 0.90, 3: 0.95, 4: 1.05, 5: 1.35, 6: 1.30}


def d2k(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def gen_dim_date() -> pd.DataFrame:
    days = pd.date_range(START, END, freq="D")
    rows = []
    for ts in days:
        d = ts.date()
        in_tet = any(a <= d <= b for a, b in TET)
        rows.append({
            "date_key": d2k(d), "date": d.isoformat(), "year": d.year, "quarter": f"Q{(d.month - 1) // 3 + 1}",
            "year_quarter": f"{d.year}-Q{(d.month - 1) // 3 + 1}", "month_number": d.month,
            "month_name": ts.strftime("%b"), "year_month": ts.strftime("%Y-%m"),
            "week_of_year": int(ts.isocalendar().week), "day_of_week": ts.weekday() + 1,
            "day_name": ts.strftime("%a"), "is_weekend": int(ts.weekday() >= 5),
            "is_holiday": int(in_tet or d in HOLIDAYS), "holiday_name": "Tet" if in_tet else ("Public holiday" if d in HOLIDAYS else None),
            "is_month_end": int((ts + pd.Timedelta(days=1)).month != ts.month),
        })
    return pd.DataFrame(rows)


def gen_dim_store() -> pd.DataFrame:
    return pd.DataFrame([{
        "store_key": i + 1, "store_code": s[0], "store_name": s[1], "channel_type": s[2], "channel": s[3],
        "city": s[4], "region": s[5], "store_format": s[6], "selling_area_sqm": s[7], "open_date": s[8].isoformat(),
    } for i, s in enumerate(STORES)])


def gen_dim_product(rng) -> pd.DataFrame:
    rows, key = [], 1
    for cat, subs in CATEGORIES.items():
        n_styles = int(round(60 * CAT_WEIGHT[cat] / 0.46))  # Women ~60 styles, Men ~44, Kids ~26
        for i in range(n_styles):
            sub, base_price = subs[i % len(subs)]
            season = "FW" if sub in ("Jacket", "Knitwear", "Jeans", "Chinos", "Pyjamas") and rng.random() < 0.7 else "SS"
            price = int(round(base_price * rng.uniform(0.85, 1.25) / 1000) * 1000) - 1000
            margin = rng.uniform(0.52, 0.64)
            for color in rng.choice(COLORS, size=rng.integers(2, 4), replace=False):
                rows.append({
                    "product_key": key, "sku": f"{cat[0]}{sub[:2].upper()}{i:03d}-{color[:3].upper()}",
                    "product_name": f"{cat} {sub} {color} #{i:03d}", "category": cat, "subcategory": sub,
                    "season": season, "color": color, "list_price": price, "unit_cost": int(round(price * (1 - margin) / 1000) * 1000),
                })
                key += 1
    return pd.DataFrame(rows)


def gen_dim_customer(rng, n=12000) -> pd.DataFrame:
    tiers = rng.choice(["Member", "Silver", "Gold"], size=n, p=[0.70, 0.22, 0.08])
    join = [START - timedelta(days=int(x)) for x in rng.integers(-700, 1500, size=n)]
    df = pd.DataFrame({
        "customer_key": np.arange(1, n + 1), "customer_id": [f"CUST{100000 + i}" for i in range(n)],
        "loyalty_tier": tiers, "gender": rng.choice(["F", "M"], size=n, p=[0.62, 0.38]),
        "age_band": rng.choice(["18-24", "25-34", "35-44", "45+"], size=n, p=[0.20, 0.42, 0.28, 0.10]),
        "city": rng.choice([s[4] for s in STORES[:12]], size=n), "join_date": [min(d, END).isoformat() for d in join],
    })
    walk_in = pd.DataFrame([{"customer_key": 0, "customer_id": "WALK-IN", "loyalty_tier": "Non-member", "gender": "unknown",
                             "age_band": "unknown", "city": "unknown", "join_date": None}])
    return pd.concat([walk_in, df], ignore_index=True)


def gen_fact_sales(rng, dates: pd.DataFrame, stores: pd.DataFrame, products: pd.DataFrame, customers: pd.DataFrame):
    prod_w = rng.pareto(1.5, size=len(products)) + 1
    prod_w /= prod_w.sum()
    season_of = products["season"].to_numpy()
    rows = []
    txn = 0
    open_dates = [datetime.fromisoformat(s[8].isoformat()).date() for s in STORES]
    for _, dr in dates.iterrows():
        d = date.fromisoformat(dr["date"])
        growth = 1.0 + 0.12 * ((d - START).days / (END - START).days)
        tet_quiet = any(a <= d <= b for a, b in TET)
        day_mult = MONTH_SEASON[d.month] * DOW[d.weekday()] * growth * (0.35 if tet_quiet else 1.0)
        if d.month == 11 and d.day == 11: day_mult *= 2.2
        if d.month == 12 and d.day == 12: day_mult *= 1.9
        for si, s in enumerate(STORES):
            if d < open_dates[si]:
                continue
            online = s[2] == "Online"
            base = 26 * STORE_WEIGHT[si] * day_mult
            if online and d.month in (11, 12):
                base *= 1.25                                   # online over-indexes in sale season
            if online and tet_quiet:
                base *= 2.0                                    # online keeps selling while stores are shut
            n_txn = rng.poisson(base)
            for _ in range(n_txn):
                txn += 1
                tid = f"T{txn:08d}"
                n_lines = rng.choice([1, 2, 3, 4], p=[0.52, 0.30, 0.13, 0.05])
                # loyalty identification: online always known; stores ~45%
                ck = int(rng.integers(1, len(customers))) if (online or rng.random() < 0.45) else 0
                # seasonal product mix: FW sells in Oct-Feb
                fw_bias = 1.6 if d.month in (10, 11, 12, 1, 2) else 0.6
                w = prod_w * np.where(season_of == "FW", fw_bias, 1.0)
                w /= w.sum()
                pks = rng.choice(len(products), size=n_lines, p=w, replace=False)
                for pk in pks:
                    qty = int(rng.choice([1, 1, 1, 2, 3], p=[0.6, 0.15, 0.1, 0.1, 0.05]))
                    price = int(products["list_price"].iloc[pk])
                    disc_rate = 0.0
                    if d.month in (11, 12) or (s[6] == "Outlet"):
                        disc_rate = float(rng.choice([0.0, 0.1, 0.2, 0.3], p=[0.25, 0.35, 0.3, 0.1]))
                    elif rng.random() < 0.15:
                        disc_rate = 0.1
                    gross = price * qty
                    disc = int(round(gross * disc_rate / 1000) * 1000)
                    rows.append((int(dr["date_key"]), si + 1, int(products["product_key"].iloc[pk]), ck, tid,
                                 qty, price, disc, gross - disc, int(products["unit_cost"].iloc[pk]) * qty))
    df = pd.DataFrame(rows, columns=["date_key", "store_key", "product_key", "customer_key", "transaction_id",
                                     "quantity", "unit_price", "discount_amount", "net_sales", "cost_amount"])
    df.insert(0, "sales_line_id", np.arange(1, len(df) + 1))
    return df


def gen_fact_inventory(rng, dates: pd.DataFrame, products: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    """Month-end stock on hand per physical store and product, loosely tied to sales velocity."""
    month_ends = dates[dates["is_month_end"] == 1]
    sold = sales.assign(ym=sales["date_key"] // 100).groupby(["ym", "store_key", "product_key"])["quantity"].sum()
    rows = []
    for _, me in month_ends.iterrows():
        ym = int(me["date_key"]) // 100
        for sk in range(1, 13):
            open_d = date.fromisoformat(STORES[sk - 1][8].isoformat())
            if date.fromisoformat(me["date"]) < open_d:
                continue
            for pk in products["product_key"]:
                monthly_units = int(sold.get((ym, sk, pk), 0))
                # target ~6 weeks of cover, with noise; FW stock piles up in spring
                cover_weeks = rng.uniform(3, 9)
                soh = max(0, int(round(monthly_units / 4.3 * cover_weeks + rng.normal(0, 2))))
                if products.loc[products["product_key"] == pk, "season"].iloc[0] == "FW" and ym % 100 in (3, 4, 5):
                    soh += int(rng.integers(3, 12))
                rows.append((int(me["date_key"]), sk, int(pk), soh))
    df = pd.DataFrame(rows, columns=["date_key", "store_key", "product_key", "stock_on_hand"])
    df = df.merge(products[["product_key", "unit_cost"]], on="product_key")
    df["stock_value_at_cost"] = df["stock_on_hand"] * df["unit_cost"]
    return df.drop(columns="unit_cost")


def gen_fact_targets(rng, sales: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    monthly = sales.assign(year_month=(sales["date_key"] // 100)).groupby(["year_month", "store_key"])["net_sales"].sum().reset_index()
    # targets set at ~ +8% on the prior-year month (or +5% on actual for 2024 as there is no history)
    rows = []
    for _, r in monthly.iterrows():
        ym, sk, actual = int(r["year_month"]), int(r["store_key"]), float(r["net_sales"])
        prev = monthly[(monthly["year_month"] == ym - 100) & (monthly["store_key"] == sk)]["net_sales"]
        base = float(prev.iloc[0]) * 1.08 if len(prev) else actual * rng.uniform(0.95, 1.12)
        rows.append({"year_month": f"{ym // 100}-{ym % 100:02d}", "store_key": sk,
                     "sales_target": int(round(base / 1_000_000) * 1_000_000)})
    return pd.DataFrame(rows)


def gen_fact_footfall(rng, dates: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    txn_per_day = sales[sales["store_key"] <= 12].groupby(["date_key", "store_key"])["transaction_id"].nunique()
    rows = []
    for (dk, sk), n in txn_per_day.items():
        conv = rng.uniform(0.18, 0.32) if STORES[sk - 1][6] != "Flagship" else rng.uniform(0.14, 0.24)
        rows.append({"date_key": int(dk), "store_key": int(sk), "footfall": int(round(n / conv))})
    return pd.DataFrame(rows)


def main():
    rng = np.random.default_rng(SEED)
    os.makedirs(OUT, exist_ok=True)
    dates = gen_dim_date()
    stores = gen_dim_store()
    products = gen_dim_product(rng)
    customers = gen_dim_customer(rng)
    sales = gen_fact_sales(rng, dates, stores, products, customers)
    inventory = gen_fact_inventory(rng, dates, products, sales)
    targets = gen_fact_targets(rng, sales, stores)
    footfall = gen_fact_footfall(rng, dates, sales)
    for name, df in [("dim_date", dates), ("dim_store", stores), ("dim_product", products), ("dim_customer", customers),
                     ("fact_sales", sales), ("fact_inventory", inventory), ("fact_targets", targets), ("fact_footfall", footfall)]:
        gz = name in ("fact_sales", "fact_inventory")
        path = os.path.join(OUT, f"{name}.csv" + (".gz" if gz else ""))
        df.to_csv(path, index=False, compression="gzip" if gz else None)
        print(f"{name:15s} {len(df):>9,} rows -> {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
