"""
Render a static preview of the Executive Overview page from the star-schema
CSVs, so the README has a visual before the .pbix screenshot is added.

    python scripts/make_preview.py      -> report/preview_executive_overview.png

The numbers are computed in pandas with the same definitions as the DAX
measures in model/measures.dax (Net Sales, YoY %, Gross Margin %,
Target Achievement %, Online Share %, Same-Store Sales Growth %).
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "star_schema")
OUT = os.path.join(ROOT, "report", "preview_executive_overview.png")

PAGE, CARD, INK, INK2, MUTED, GRID = "#f9f9f7", "#ffffff", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE, ORANGE, AQUA, YELLOW, GOOD, BAD = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#0ca30c", "#d03b3b"
CHANNEL_COLORS = {"Physical store": BLUE, "Website": ORANGE, "Mobile app": AQUA, "Marketplace": YELLOW}

plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.facecolor": CARD, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True})


def load():
    s = pd.read_csv(os.path.join(D, "fact_sales.csv.gz"))
    st = pd.read_csv(os.path.join(D, "dim_store.csv"))
    p = pd.read_csv(os.path.join(D, "dim_product.csv"))
    t = pd.read_csv(os.path.join(D, "fact_targets.csv"))
    s = s.merge(st, on="store_key").merge(p[["product_key", "category"]], on="product_key")
    s["year"] = s.date_key // 10000
    s["ym"] = (s.date_key // 100).astype(str).str.replace(r"(\d{4})(\d{2})", r"\1-\2", regex=True)
    return s, st, t


def card(ax, title, value, sub=None, sub_color=INK2):
    ax.set_axis_off()
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.06", fc=CARD, ec=GRID, lw=1,
                                transform=ax.transAxes))
    ax.text(0.07, 0.72, title, color=INK2, fontsize=9, transform=ax.transAxes)
    ax.text(0.07, 0.34, value, color=INK, fontsize=20, fontweight="bold", transform=ax.transAxes)
    if sub:
        ax.text(0.07, 0.10, sub, color=sub_color, fontsize=9, transform=ax.transAxes)


def main():
    s, st, t = load()
    y24, y25 = s[s.year == 2024], s[s.year == 2025]
    net24, net25 = y24.net_sales.sum(), y25.net_sales.sum()
    yoy = net25 / net24 - 1
    gm = 1 - y25.cost_amount.sum() / net25
    online = y25[y25.channel_type == "Online"].net_sales.sum() / net25
    comp = st[(st.channel_type == "Store") & (st.open_date <= "2024-01-01")].store_key
    ss24, ss25 = y24[y24.store_key.isin(comp)].net_sales.sum(), y25[y25.store_key.isin(comp)].net_sales.sum()
    ssg = ss25 / ss24 - 1
    m = s.groupby(["ym", "store_key"]).net_sales.sum().reset_index().merge(t.rename(columns={"year_month": "ym"}), on=["ym", "store_key"])
    m25 = m[m.ym >= "2025"]
    ach = m25.net_sales.sum() / m25.sales_target.sum()

    fig = plt.figure(figsize=(14, 8), facecolor=PAGE)
    gs = fig.add_gridspec(nrows=3, ncols=5, height_ratios=[1.1, 2.6, 2.4], hspace=0.55, wspace=0.28,
                          left=0.04, right=0.98, top=0.86, bottom=0.08)

    # header
    fig.text(0.04, 0.95, "Omnichannel Retail — Executive Overview", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.04, 0.915, "01 Jan 2025 - 31 Dec 2025  ·  All regions  ·  All channels  ·  Data to 31 Dec 2025", fontsize=9.5, color=MUTED)
    fig.text(0.98, 0.95, "PREVIEW rendered from the CSV data — not a Power BI screenshot", fontsize=8, color=MUTED, ha="right")

    # KPI cards
    card(fig.add_subplot(gs[0, 0]), "Net Sales", f"{net25 / 1e9:.1f} B VND", f"▲ {yoy:+.1%} vs LY", GOOD)
    card(fig.add_subplot(gs[0, 1]), "Gross Margin %", f"{gm:.1%}", "Target 55%", INK2)
    card(fig.add_subplot(gs[0, 2]), "Target Achievement", f"{ach:.1%}", f"▼ {(ach - 1) * 100:+.1f} pts vs plan", BAD)
    card(fig.add_subplot(gs[0, 3]), "Online Share", f"{online:.1%}", "Website + App + Marketplace", INK2)
    card(fig.add_subplot(gs[0, 4]), "Same-Store Sales Growth", f"{ssg:+.1%}", "10 comparable stores", GOOD)

    # trend line: 2025 vs LY
    ax = fig.add_subplot(gs[1, 0:3])
    mon = s.groupby(["year", s.date_key // 100 % 100]).net_sales.sum().unstack(0) / 1e9
    x = np.arange(1, 13)
    ax.plot(x, mon[2024], color=MUTED, lw=1.5, label="Net Sales LY")
    ax.plot(x, mon[2025], color=BLUE, lw=2.2, marker="o", ms=3.5, label="Net Sales")
    ax.set_xticks(x); ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_ylim(0); ax.grid(axis="y"); ax.set_title("Net sales by month vs last year (B VND)", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=8.5)
    ax.annotate("Tet", (2, mon[2025][2]), textcoords="offset points", xytext=(14, 4), ha="left", color=MUTED, fontsize=8)
    ax.annotate("11.11", (11, mon[2025][11]), textcoords="offset points", xytext=(0, 7), ha="center", color=INK2, fontsize=8)

    # target by region
    ax = fig.add_subplot(gs[1, 3:5])
    reg = m25.merge(st[["store_key", "region"]], on="store_key").groupby("region")[["net_sales", "sales_target"]].sum().div(1e9)
    reg = reg.reindex(["North", "South", "Central", "Online"])
    yy = np.arange(len(reg)); h = 0.36
    ax.barh(yy + h / 2, reg.net_sales, h, color=BLUE, label="Net Sales")
    ax.barh(yy - h / 2, reg.sales_target, h, color="#c3c2b7", label="Sales Target")
    for i, (a, b) in enumerate(zip(reg.net_sales, reg.sales_target)):
        ax.text(max(a, b) + 0.5, i, f"{a / b:.0%}", va="center", fontsize=8.5, color=GOOD if a >= b else BAD)
    ax.set_yticks(yy); ax.set_yticklabels(reg.index); ax.invert_yaxis(); ax.grid(axis="x")
    ax.set_title("Net sales vs target by region (B VND)", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=8.5)

    # channel mix 100% stacked per year
    ax = fig.add_subplot(gs[2, 0:2])
    mix = s.groupby(["year", "channel"]).net_sales.sum().unstack(1)
    mix = mix.div(mix.sum(axis=1), axis=0)[list(CHANNEL_COLORS)]
    left = np.zeros(len(mix))
    for ch in mix.columns:
        ax.barh(mix.index.astype(str), mix[ch], left=left, color=CHANNEL_COLORS[ch], label=ch, height=0.55, edgecolor=CARD, linewidth=2)
        for i, (l, v) in enumerate(zip(left, mix[ch])):
            if v > 0.06:
                ax.text(l + v / 2, i, f"{v:.0%}", ha="center", va="center", fontsize=8.5, color="#ffffff" if ch != "Marketplace" else INK)
        left += mix[ch].to_numpy()
    ax.set_xlim(0, 1); ax.set_xticks([]); ax.grid(False); ax.spines["bottom"].set_visible(False)
    ax.set_title("Channel mix by year", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=4, fontsize=8.5)

    # category: 2025 vs LY
    ax = fig.add_subplot(gs[2, 2:4])
    cat = s.groupby(["category", "year"]).net_sales.sum().unstack(1).div(1e9).loc[["Women", "Men", "Kids"]]
    xx = np.arange(3); w = 0.36
    ax.bar(xx - w / 2, cat[2024], w, color="#c3c2b7", label="LY")
    ax.bar(xx + w / 2, cat[2025], w, color=BLUE, label="2025")
    for i in xx:
        ax.text(i + w / 2, cat[2025].iloc[i] + 0.8, f"{cat[2025].iloc[i] / cat[2024].iloc[i] - 1:+.1%}", ha="center", fontsize=8.5, color=INK2)
    ax.set_xticks(xx); ax.set_xticklabels(cat.index); ax.set_ylim(0, cat.values.max() * 1.2); ax.grid(axis="y")
    ax.set_title("Net sales by category (B VND)", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.legend(frameon=False, fontsize=8.5)

    # store league mini-table
    ax = fig.add_subplot(gs[2, 4]); ax.set_axis_off()
    ax.set_title("Stores below target (2025)", loc="left", fontsize=11, fontweight="bold", color=INK)
    lg = m25.groupby("store_key")[["net_sales", "sales_target"]].sum()
    lg["ach"] = lg.net_sales / lg.sales_target
    lg = lg.merge(st[["store_key", "store_name"]], left_index=True, right_on="store_key").sort_values("ach").head(6)
    for i, (_, r) in enumerate(lg.iterrows()):
        ax.text(0.0, 0.9 - i * 0.16, r.store_name, fontsize=8.5, color=INK, transform=ax.transAxes)
        ax.text(1.0, 0.9 - i * 0.16, f"{r.ach:.1%}", fontsize=8.5, color=BAD, ha="right", transform=ax.transAxes)
        ax.plot([0, 1], [0.86 - i * 0.16] * 2, color=GRID, lw=0.8, transform=ax.transAxes)

    fig.savefig(OUT, dpi=150, facecolor=PAGE)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
