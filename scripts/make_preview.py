"""
Render static previews of the five report pages from the star-schema CSVs.

    python scripts/make_preview.py      -> report/preview_1_executive.png ... preview_5_customers.png

Numbers are computed in pandas with the same definitions as the DAX measures in
model/measures.dax (and the JavaScript in docs/index.html). The live, filterable
version of the same pages is the web dashboard in docs/.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "star_schema")
REPORT = os.path.join(ROOT, "report")

PAGE, CARD, INK, INK2, MUTED, GRID = "#f9f9f7", "#ffffff", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, LY, GOOD, BAD = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#c3c2b7", "#0ca30c", "#d03b3b"
CHANNEL_COLORS = {"Physical store": BLUE, "Website": ORANGE, "Mobile app": AQUA, "Marketplace": YELLOW}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
YEAR = 2025

plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.facecolor": CARD, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "axes.titlelocation": "left", "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlecolor": INK})


# ------------------------------------------------------------------ data
def load():
    s = pd.read_csv(os.path.join(D, "fact_sales.csv.gz"))
    st = pd.read_csv(os.path.join(D, "dim_store.csv"))
    p = pd.read_csv(os.path.join(D, "dim_product.csv"))
    c = pd.read_csv(os.path.join(D, "dim_customer.csv"))
    t = pd.read_csv(os.path.join(D, "fact_targets.csv"))
    f = pd.read_csv(os.path.join(D, "fact_footfall.csv"))
    inv = pd.read_csv(os.path.join(D, "fact_inventory.csv.gz")).merge(p[["product_key", "season", "subcategory", "category"]], on="product_key")
    s = s.merge(st, on="store_key").merge(p[["product_key", "category", "subcategory", "season", "sku"]], on="product_key").merge(c[["customer_key", "loyalty_tier", "age_band", "gender"]], on="customer_key", how="left")
    s["year"] = s.date_key // 10000
    s["ym"] = (s.date_key // 100).astype(str).str.replace(r"(\d{4})(\d{2})", r"\1-\2", regex=True)
    s["month"] = s.date_key // 100 % 100
    inv["ym"] = (inv.date_key // 100).astype(str).str.replace(r"(\d{4})(\d{2})", r"\1-\2", regex=True)
    return s, st, p, c, t, f, inv


# ------------------------------------------------------------------ helpers
def card(ax, title, value, sub=None, sub_color=INK2):
    ax.set_axis_off()
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.06", fc=CARD, ec=GRID, lw=1, transform=ax.transAxes))
    ax.text(0.07, 0.72, title, color=INK2, fontsize=9, transform=ax.transAxes)
    ax.text(0.07, 0.34, value, color=INK, fontsize=19, fontweight="bold", transform=ax.transAxes)
    if sub:
        ax.text(0.07, 0.10, sub, color=sub_color, fontsize=8.5, transform=ax.transAxes)


def page(title, filters="01 Jan 2025 - 31 Dec 2025  ·  All regions  ·  All channels  ·  All categories"):
    fig = plt.figure(figsize=(14, 8), facecolor=PAGE)
    fig.text(0.04, 0.95, f"Omnichannel Retail — {title}", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.04, 0.915, f"{filters}  ·  Data to 31 Dec 2025", fontsize=9.5, color=MUTED)
    fig.text(0.98, 0.95, "Static preview rendered from the data (Python) — interactive version in docs/", fontsize=8, color=MUTED, ha="right")
    gs = fig.add_gridspec(nrows=3, ncols=5, height_ratios=[1.1, 2.6, 2.4], hspace=0.6, wspace=0.3, left=0.04, right=0.98, top=0.86, bottom=0.08)
    return fig, gs


def save(fig, name):
    path = os.path.join(REPORT, name)
    fig.savefig(path, dpi=150, facecolor=PAGE)
    plt.close(fig)
    print("  wrote", os.path.relpath(path, ROOT))


def mini_table(ax, title, rows, color_fn=None):
    ax.set_axis_off()
    ax.set_title(title)
    for i, (label, value) in enumerate(rows):
        ax.text(0.0, 0.9 - i * 0.16, label, fontsize=8.5, color=INK, transform=ax.transAxes)
        ax.text(1.0, 0.9 - i * 0.16, value, fontsize=8.5, color=color_fn(value) if color_fn else INK2, ha="right", transform=ax.transAxes)
        ax.plot([0, 1], [0.86 - i * 0.16] * 2, color=GRID, lw=0.8, transform=ax.transAxes)


# ------------------------------------------------------------------ page 1
def page1(s, st, t):
    y24, y25 = s[s.year == 2024], s[s.year == 2025]
    net24, net25 = y24.net_sales.sum(), y25.net_sales.sum()
    gm = 1 - y25.cost_amount.sum() / net25
    online = y25[y25.channel_type == "Online"].net_sales.sum() / net25
    comp = st[(st.channel_type == "Store") & (st.open_date <= "2024-01-01")].store_key
    ssg = y25[y25.store_key.isin(comp)].net_sales.sum() / y24[y24.store_key.isin(comp)].net_sales.sum() - 1
    m = s.groupby(["ym", "store_key"]).net_sales.sum().reset_index().merge(t.rename(columns={"year_month": "ym"}), on=["ym", "store_key"])
    m25 = m[m.ym >= "2025"]
    ach = m25.net_sales.sum() / m25.sales_target.sum()

    fig, gs = page("Executive Overview")
    card(fig.add_subplot(gs[0, 0]), "Net Sales", f"{net25 / 1e9:.1f} B VND", f"▲ {net25 / net24 - 1:+.1%} vs LY", GOOD)
    card(fig.add_subplot(gs[0, 1]), "Gross Margin %", f"{gm:.1%}", "Target 55%")
    card(fig.add_subplot(gs[0, 2]), "Target Achievement", f"{ach:.1%}", f"▼ {(ach - 1) * 100:+.1f} pts vs plan", BAD)
    card(fig.add_subplot(gs[0, 3]), "Online Share", f"{online:.1%}", "Website + App + Marketplace")
    card(fig.add_subplot(gs[0, 4]), "Same-Store Sales Growth", f"{ssg:+.1%}", f"{len(comp)} comparable stores", GOOD)

    ax = fig.add_subplot(gs[1, 0:3])
    mon = s.groupby(["year", "month"]).net_sales.sum().unstack(0) / 1e9
    x = np.arange(1, 13)
    ax.plot(x, mon[2024], color=LY, lw=1.5, label="Net Sales LY")
    ax.plot(x, mon[2025], color=BLUE, lw=2.2, marker="o", ms=3.5, label="Net Sales")
    ax.set_xticks(x); ax.set_xticklabels(MONTHS); ax.set_ylim(0); ax.grid(axis="y")
    ax.set_title("Net sales by month vs last year (B VND)"); ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=8.5)

    ax = fig.add_subplot(gs[1, 3:5])
    reg = m25.merge(st[["store_key", "region"]], on="store_key").groupby("region")[["net_sales", "sales_target"]].sum().div(1e9).reindex(["North", "South", "Central", "Online"])
    yy = np.arange(len(reg)); h = 0.36
    ax.barh(yy + h / 2, reg.net_sales, h, color=BLUE, label="Net Sales"); ax.barh(yy - h / 2, reg.sales_target, h, color=LY, label="Sales Target")
    for i, (a, b) in enumerate(zip(reg.net_sales, reg.sales_target)):
        ax.text(max(a, b) + 0.5, i, f"{a / b:.0%}", va="center", fontsize=8.5, color=GOOD if a >= b else BAD)
    ax.set_yticks(yy); ax.set_yticklabels(reg.index); ax.invert_yaxis(); ax.grid(axis="x")
    ax.set_title("Net sales vs target by region (B VND)"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=8.5)

    ax = fig.add_subplot(gs[2, 0:2])
    mix = s.groupby(["year", "channel"]).net_sales.sum().unstack(1); mix = mix.div(mix.sum(axis=1), axis=0)[list(CHANNEL_COLORS)]
    left = np.zeros(len(mix))
    for ch in mix.columns:
        ax.barh(mix.index.astype(str), mix[ch], left=left, color=CHANNEL_COLORS[ch], label=ch, height=0.55, edgecolor=CARD, linewidth=2)
        for i, (l, v) in enumerate(zip(left, mix[ch])):
            if v > 0.06:
                ax.text(l + v / 2, i, f"{v:.0%}", ha="center", va="center", fontsize=8.5, color="#ffffff" if ch != "Marketplace" else INK)
        left += mix[ch].to_numpy()
    ax.set_xlim(0, 1); ax.set_xticks([]); ax.grid(False); ax.spines["bottom"].set_visible(False)
    ax.set_title("Channel mix by year"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=4, fontsize=8.5)

    ax = fig.add_subplot(gs[2, 2:4])
    cat = s.groupby(["category", "year"]).net_sales.sum().unstack(1).div(1e9).loc[["Women", "Men", "Kids"]]
    xx = np.arange(3); w = 0.36
    ax.bar(xx - w / 2, cat[2024], w, color=LY, label="LY"); ax.bar(xx + w / 2, cat[2025], w, color=BLUE, label="2025")
    for i in xx:
        ax.text(i + w / 2, cat[2025].iloc[i] + 0.8, f"{cat[2025].iloc[i] / cat[2024].iloc[i] - 1:+.1%}", ha="center", fontsize=8.5, color=INK2)
    ax.set_xticks(xx); ax.set_xticklabels(cat.index); ax.set_ylim(0, cat.values.max() * 1.2); ax.grid(axis="y")
    ax.set_title("Net sales by category (B VND)"); ax.legend(frameon=False, fontsize=8.5)

    lg = m25.groupby("store_key")[["net_sales", "sales_target"]].sum(); lg["ach"] = lg.net_sales / lg.sales_target
    lg = lg.merge(st[["store_key", "store_name"]], left_index=True, right_on="store_key").sort_values("ach").head(6)
    mini_table(fig.add_subplot(gs[2, 4]), "Locations below target (2025)", [(r.store_name, f"{r.ach:.1%}") for _, r in lg.iterrows()], lambda v: BAD)
    save(fig, "preview_1_executive.png")


# ------------------------------------------------------------------ page 2
def page2(s):
    y25 = s[s.year == 2025]
    ch = y25.groupby("channel").agg(net=("net_sales", "sum"), gross=("unit_price", lambda x: (x * y25.loc[x.index, "quantity"]).sum()), cost=("cost_amount", "sum"), tx=("transaction_id", "nunique"), units=("quantity", "sum")).reindex(list(CHANNEL_COLORS))
    ch["basket"] = ch.net / ch.tx; ch["disc"] = 1 - ch.net / ch.gross; ch["gm"] = 1 - ch.cost / ch.net
    online = y25[y25.channel_type == "Online"].net_sales.sum(); online_ly = s[(s.year == 2024) & (s.channel_type == "Online")].net_sales.sum()

    fig, gs = page("Channel Performance")
    card(fig.add_subplot(gs[0, 0]), "Online Net Sales", f"{online / 1e9:.1f} B VND", f"▲ {online / online_ly - 1:+.1%} vs LY", GOOD)
    card(fig.add_subplot(gs[0, 1]), "Online Share", f"{online / y25.net_sales.sum():.1%}", "of total net sales")
    card(fig.add_subplot(gs[0, 2]), "Highest Avg Basket", f"{ch.basket.max() / 1e3:,.0f} K", ch.basket.idxmax())
    card(fig.add_subplot(gs[0, 3]), "Highest Discount Rate", f"{ch.disc.max():.1%}", f"{ch.disc.idxmax()} · GM {ch.loc[ch.disc.idxmax(), 'gm']:.1%}")
    card(fig.add_subplot(gs[0, 4]), "Transactions", f"{ch.tx.sum():,}", "2025")

    ax = fig.add_subplot(gs[1, 0:3])
    mon = y25.groupby(["channel", "month"]).net_sales.sum().unstack(0) / 1e9
    for c in CHANNEL_COLORS:
        ax.plot(np.arange(1, 13), mon[c], color=CHANNEL_COLORS[c], lw=2, label=c)
    ax.set_xticks(np.arange(1, 13)); ax.set_xticklabels(MONTHS); ax.set_ylim(0); ax.grid(axis="y")
    ax.set_title("Monthly net sales by channel (B VND)"); ax.legend(frameon=False, ncol=4, fontsize=8.5, loc="upper center")

    ax = fig.add_subplot(gs[1, 3:5])
    ax.bar(ch.index, ch.basket / 1e3, color=[CHANNEL_COLORS[c] for c in ch.index], width=0.6)
    for i, v in enumerate(ch.basket / 1e3):
        ax.text(i, v + 8, f"{v:,.0f} K", ha="center", fontsize=8.5, color=INK2)
    ax.set_ylim(0, ch.basket.max() / 1e3 * 1.2); ax.grid(axis="y"); ax.tick_params(axis="x", labelsize=8)
    ax.set_title("Average basket value by channel (K VND)")

    ax = fig.add_subplot(gs[2, 0:3])
    loc = y25.groupby(["store_name", "channel_type"]).agg(net=("net_sales", "sum"), cost=("cost_amount", "sum"), gross=("unit_price", lambda x: (x * y25.loc[x.index, "quantity"]).sum())).reset_index()
    loc["disc"] = 1 - loc.net / loc.gross; loc["gm"] = 1 - loc.cost / loc.net
    for tp, col, lab in (("Store", BLUE, "Physical store"), ("Online", ORANGE, "Online channel")):
        g = loc[loc.channel_type == tp]
        ax.scatter(g.disc * 100, g.gm * 100, s=30 + np.sqrt(g.net / 1e9) * 120, color=col, alpha=0.8, edgecolor="white", linewidth=1, label=lab)
    for i, (_, r) in enumerate(loc[(loc.disc > 0.08) | (loc.gm < 0.54)].sort_values("gm").iterrows()):
        ax.annotate(r.store_name, (r.disc * 100, r.gm * 100), textcoords="offset points", xytext=(-10, 14 if i % 2 else -4), ha="right", fontsize=7.5, color=INK2)
    ax.text(0.03, 0.06, "Cluster: 13 locations at 4–5% discount, 55–56% margin", transform=ax.transAxes, fontsize=8, color=MUTED)
    ax.set_xlabel("Discount rate (%)"); ax.set_ylabel("Gross margin (%)"); ax.grid(True)
    ax.set_title("Discount rate vs gross margin by location (bubble = net sales)"); ax.legend(frameon=False, fontsize=8.5)

    ax = fig.add_subplot(gs[2, 3:5])
    d = s[(s.year == 2025) & (s.month <= 2)].groupby(["date_key", "channel_type"]).net_sales.sum().unstack(1) / 1e6
    dates = pd.to_datetime(d.index.astype(str))
    ax.plot(dates, d["Store"], color=BLUE, lw=1.8, label="Physical stores"); ax.plot(dates, d["Online"], color=ORANGE, lw=1.8, label="Online")
    ax.axvspan(pd.Timestamp("2025-01-25"), pd.Timestamp("2025-02-02"), color=GRID, alpha=0.7, lw=0)
    ax.text(pd.Timestamp("2025-01-29"), ax.get_ylim()[1] * 0.92, "Tet", ha="center", fontsize=8.5, color=INK2)
    ax.set_ylim(0); ax.grid(axis="y")
    ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=10)); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b")); ax.tick_params(axis="x", labelsize=8)
    ax.set_title("Daily net sales through Tet (M VND)"); ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    save(fig, "preview_2_channel.png")


# ------------------------------------------------------------------ page 3
def page3(s, st, t, f):
    y25 = s[s.year == 2025]
    rows = y25.groupby("store_key").agg(net=("net_sales", "sum"), tx=("transaction_id", "nunique")).merge(st, on="store_key")
    ly = s[s.year == 2024].groupby("store_key").net_sales.sum()
    tg = t[t.year_month >= "2025"].groupby("store_key").sales_target.sum()
    ff = f[f.date_key // 10000 == 2025].groupby("store_key").footfall.sum()
    rows["ly"] = rows.store_key.map(ly); rows["tgt"] = rows.store_key.map(tg); rows["ff"] = rows.store_key.map(ff)
    rows["ach"] = rows.net / rows.tgt; rows["yoy"] = rows.net / rows.ly - 1; rows["psqm"] = rows.net / rows.selling_area_sqm.replace(0, np.nan); rows["conv"] = rows.tx / rows.ff
    stores = rows[rows.channel_type == "Store"]

    fig, gs = page("Store Performance")
    card(fig.add_subplot(gs[0, 0]), "Locations below target", f"{(rows.ach < 1).sum()} / {len(rows)}", "2025", BAD)
    card(fig.add_subplot(gs[0, 1]), "Conversion Rate", f"{stores.tx.sum() / stores.ff.sum():.1%}", "store transactions ÷ footfall")
    card(fig.add_subplot(gs[0, 2]), "Best sales per sqm", f"{stores.psqm.max() / 1e6:.1f} M", stores.loc[stores.psqm.idxmax(), "store_name"])
    card(fig.add_subplot(gs[0, 3]), "Lowest sales per sqm", f"{stores.psqm.min() / 1e6:.1f} M", f"{stores.loc[stores.psqm.idxmin(), 'store_name']} · Outlet", BAD)
    card(fig.add_subplot(gs[0, 4]), "Avg basket (stores)", f"{stores.net.sum() / stores.tx.sum() / 1e3:,.0f} K", "per transaction")

    ax = fig.add_subplot(gs[1, 0:3]); ax.set_axis_off(); ax.set_title("Store league table (sorted by target achievement)")
    tbl = rows.sort_values("ach")[["store_name", "store_format", "net", "yoy", "ach", "psqm", "conv"]].head(9)
    cells = [[r.store_name, r.store_format, f"{r.net / 1e9:.1f} B", "new" if pd.isna(r.yoy) else f"{r.yoy:+.1%}", f"{r.ach:.1%}", "–" if pd.isna(r.psqm) else f"{r.psqm / 1e6:.1f} M", "–" if pd.isna(r.conv) else f"{r.conv:.1%}"] for _, r in tbl.iterrows()]
    table = ax.table(cellText=cells, colLabels=["Location", "Format", "Net sales", "YoY", "Target", "Sales/sqm", "Conv."], bbox=[0, 0, 1, 1], cellLoc="right", colLoc="right",
                     colWidths=[0.30, 0.14, 0.13, 0.11, 0.11, 0.12, 0.09])
    table.auto_set_font_size(False); table.set_fontsize(7.5)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(GRID); cell.set_linewidth(0.6)
        if r == 0:
            cell.set_text_props(color=INK2, fontweight="bold"); cell.set_facecolor(CARD)
        if c in (0, 1):
            cell.get_text().set_ha("left")
        if r > 0 and c == 4:
            cell.get_text().set_color(BAD if float(cells[r - 1][4].rstrip("%")) < 100 else GOOD)

    ax = fig.add_subplot(gs[1, 3:5])
    sq = stores.sort_values("psqm")
    ax.barh(sq.store_name.str.replace("Ho Chi Minh City", "HCMC"), sq.psqm / 1e6, color=BLUE, height=0.6)
    for i, (v, fmt) in enumerate(zip(sq.psqm / 1e6, sq.store_format)):
        ax.text(v + 0.3, i, fmt, va="center", fontsize=7.5, color=MUTED)
    ax.grid(axis="x"); ax.tick_params(axis="y", labelsize=8); ax.set_xlim(0, sq.psqm.max() / 1e6 * 1.25)
    ax.set_title("Sales per sqm (M VND)")

    ax = fig.add_subplot(gs[2, 0:2])
    ax.scatter(stores.ff / 1e3, stores.conv * 100, s=30 + np.sqrt(stores.net / 1e9) * 120, color=BLUE, alpha=0.8, edgecolor="white")
    for i, (_, r) in enumerate(stores.sort_values("ff").iterrows()):
        ax.annotate(r.store_name.split(" - ")[0], (r.ff / 1e3, r.conv * 100), textcoords="offset points", xytext=(0, 9 if i % 2 == 0 else -13), ha="center", fontsize=7, color=INK2)
    ax.set_xlabel("Footfall (thousand)"); ax.set_ylabel("Conversion (%)"); ax.grid(True); ax.margins(y=0.25)
    ax.set_title("Conversion rate vs footfall (bubble = net sales)")

    ax = fig.add_subplot(gs[2, 2:5]); ax.grid(False)
    m = y25.groupby(["store_key", "month"]).net_sales.sum().unstack(1)
    tm = t[t.year_month >= "2025"].assign(month=lambda d: d.year_month.str[5:].astype(int)).pivot(index="store_key", columns="month", values="sales_target")
    z = (m / tm - 1) * 100
    z = z.loc[rows.sort_values("ach").store_key]
    im = ax.imshow(z.to_numpy(), cmap=matplotlib.colors.LinearSegmentedColormap.from_list("div", [BAD, "#f0efec", BLUE]), vmin=-15, vmax=15, aspect="auto")
    ax.set_xticks(range(12)); ax.set_xticklabels(MONTHS, fontsize=8); ax.set_yticks(range(len(z))); ax.set_yticklabels(rows.set_index("store_key").loc[z.index, "store_name"], fontsize=7.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02); cb.set_label("% vs target", color=INK2); cb.outline.set_visible(False)
    ax.set_title("Target achievement by location and month")
    save(fig, "preview_3_store.png")


# ------------------------------------------------------------------ page 4
def page4(s, inv):
    y25 = s[(s.year == 2025) & (s.channel_type == "Store")]
    inv_dec = inv[inv.date_key == 20251231]; inv_apr = inv[inv.date_key == 20250430]
    units = y25.quantity.sum(); soh = inv_dec.stock_on_hand.sum()
    st = units / (units + soh); woc = soh / (units / 52.14)
    fw_apr = inv_apr[inv_apr.season == "FW"].stock_on_hand.sum() / (y25[(y25.month == 4) & (y25.season == "FW")].quantity.sum() / 4.345)

    fig, gs = page("Product & Inventory")
    card(fig.add_subplot(gs[0, 0]), "Sell-Through", f"{st:.1%}", "2025 · physical stores", GOOD)
    card(fig.add_subplot(gs[0, 1]), "Weeks of Cover", f"{woc:.1f}", "closing stock Dec 2025")
    card(fig.add_subplot(gs[0, 2]), "Stock Value at Cost", f"{inv_dec.stock_value_at_cost.sum() / 1e9:.1f} B VND", "month-end Dec 2025")
    card(fig.add_subplot(gs[0, 3]), "FW Weeks of Cover · Apr", f"{fw_apr:.1f}", "end-of-season overhang", BAD)
    card(fig.add_subplot(gs[0, 4]), "Units Sold (stores)", f"{units:,}", "2025")

    ax = fig.add_subplot(gs[1, 0:2])
    sold = y25.groupby(["subcategory", "season"]).quantity.sum(); stock = inv_dec.groupby(["subcategory", "season"]).stock_on_hand.sum()
    stv = (sold / (sold + stock)).unstack(1).sort_values("SS")
    yy = np.arange(len(stv)); h = 0.38
    ax.barh(yy + h / 2, stv["SS"] * 100, h, color=BLUE, label="Spring/Summer"); ax.barh(yy - h / 2, stv["FW"].fillna(0) * 100, h, color=ORANGE, label="Fall/Winter")
    ax.set_yticks(yy); ax.set_yticklabels(stv.index, fontsize=8); ax.set_xlim(0, 100); ax.grid(axis="x")
    ax.set_title("Sell-through by subcategory (%)"); ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2)

    ax = fig.add_subplot(gs[1, 2:5])
    for season, col in (("SS", BLUE), ("FW", ORANGE)):
        u = y25[y25.season == season].groupby("month").quantity.sum()
        so = inv[(inv.date_key // 10000 == 2025) & (inv.season == season)].groupby(inv.date_key // 100 % 100).stock_on_hand.sum()
        ax.plot(np.arange(1, 13), (so / (u / 4.345)).reindex(range(1, 13)), color=col, lw=2, marker="o", ms=3.5, label="Spring/Summer" if season == "SS" else "Fall/Winter")
    ax.axhline(6, color=MUTED, lw=1, ls="--"); ax.text(1.0, 6.4, "6-week target", fontsize=8, color=MUTED, va="bottom")
    ax.set_xticks(np.arange(1, 13)); ax.set_xticklabels(MONTHS); ax.set_ylim(0); ax.grid(axis="y")
    ax.set_title("Weeks of cover by season"); ax.legend(frameon=False, fontsize=8.5)

    sk = s[s.year == 2025].groupby(["sku", "category", "subcategory"]).agg(net=("net_sales", "sum"), units=("quantity", "sum")).reset_index().sort_values("net", ascending=False).head(8)
    mini_table(fig.add_subplot(gs[2, 0:2]), "Top SKUs by net sales (2025)", [(f"{r.sku}  ·  {r.category} {r.subcategory}", f"{r.net / 1e6:,.0f} M") for _, r in sk.iterrows()])

    ax = fig.add_subplot(gs[2, 2:5])
    sub = s[s.year == 2025].groupby(["category", "subcategory"]).net_sales.sum().div(1e9).sort_values(ascending=False)
    colors = [{"Women": BLUE, "Men": ORANGE, "Kids": AQUA}[c] for c, _ in sub.index]
    ax.bar(range(len(sub)), sub.values, color=colors, width=0.7)
    ax.set_xticks(range(len(sub))); ax.set_xticklabels([f"{c[:1]}·{sc}" for c, sc in sub.index], rotation=45, ha="right", fontsize=7.5); ax.grid(axis="y")
    ax.set_title("Net sales by subcategory (B VND) — colour = category")
    for c, col in (("Women", BLUE), ("Men", ORANGE), ("Kids", AQUA)):
        ax.bar([0], [0], color=col, label=c)
    ax.legend(frameon=False, fontsize=8.5, ncol=3)
    save(fig, "preview_4_product.png")


# ------------------------------------------------------------------ page 5
def page5(s, c):
    y25 = s[s.year == 2025]; ident = y25[y25.customer_key > 0]
    per = ident.groupby(["customer_key", "loyalty_tier"]).transaction_id.nunique().reset_index()
    n_cust = per.customer_key.nunique(); repeat = (per.transaction_id >= 2).sum()

    fig, gs = page("Customers & Loyalty")
    card(fig.add_subplot(gs[0, 0]), "Identified Customers", f"{n_cust:,}", "2025")
    card(fig.add_subplot(gs[0, 1]), "Identified Sales Share", f"{ident.net_sales.sum() / y25.net_sales.sum():.1%}", "online = 100% by design")
    card(fig.add_subplot(gs[0, 2]), "Loyalty Share", f"{ident[ident.loyalty_tier.isin(['Silver', 'Gold'])].net_sales.sum() / y25.net_sales.sum():.1%}", "Silver + Gold tiers")
    card(fig.add_subplot(gs[0, 3]), "Repeat Rate", f"{repeat / n_cust:.1%}", "2+ transactions in the year")
    card(fig.add_subplot(gs[0, 4]), "Avg Spend / Identified Customer", f"{ident.net_sales.sum() / n_cust / 1e3:,.0f} K", "net sales ÷ customers")

    ax = fig.add_subplot(gs[1, 0:2])
    share = y25.groupby("channel").apply(lambda g: g.loc[g.customer_key > 0, "net_sales"].sum() / g.net_sales.sum(), include_groups=False).reindex(list(CHANNEL_COLORS))
    ax.bar(share.index, share * 100, color=[CHANNEL_COLORS[x] for x in share.index], width=0.6)
    for i, v in enumerate(share * 100):
        ax.text(i, v + 2, f"{v:.0f}%", ha="center", fontsize=8.5, color=INK2)
    ax.set_ylim(0, 115); ax.grid(axis="y"); ax.tick_params(axis="x", labelsize=8)
    ax.set_title("Identified sales share by channel (%)")

    ax = fig.add_subplot(gs[1, 2:5])
    rr = per.groupby("loyalty_tier").transaction_id.apply(lambda x: (x >= 2).mean()).reindex(["Member", "Silver", "Gold"])
    tn = ident.groupby("loyalty_tier").net_sales.sum().reindex(["Member", "Silver", "Gold"]) / 1e9
    ax.bar(rr.index, rr * 100, color=["#9ec5f4", "#5598e7", "#1c5cab"], width=0.55)
    for i, (v, n) in enumerate(zip(rr * 100, tn)):
        ax.text(i, v + 2, f"{v:.0f}%  ·  {n:.1f} B", ha="center", fontsize=8.5, color=INK2)
    ax.set_ylim(0, 100); ax.grid(axis="y")
    ax.set_title("Repeat rate by loyalty tier (label: repeat % · net sales)")

    ax = fig.add_subplot(gs[2, 0:3])
    age = ident.groupby(["age_band", "gender"]).net_sales.sum().unstack(1).div(1e9).reindex(["18-24", "25-34", "35-44", "45+"])
    xx = np.arange(len(age)); w = 0.38
    ax.bar(xx - w / 2, age["F"], w, color=MAGENTA, label="Female"); ax.bar(xx + w / 2, age["M"], w, color=BLUE, label="Male")
    ax.set_xticks(xx); ax.set_xticklabels(age.index); ax.grid(axis="y")
    ax.set_title("Identified net sales by age band and gender (B VND)"); ax.legend(frameon=False, fontsize=8.5)

    ax = fig.add_subplot(gs[2, 3:5])
    joins = c[(c.customer_key > 0) & (c.join_date >= "2025-01-01")].assign(m=lambda d: d.join_date.str[5:7].astype(int)).groupby("m").size().reindex(range(1, 13), fill_value=0)
    ax.bar(np.arange(1, 13), joins.values, color=BLUE, width=0.65)
    ax.set_xticks(np.arange(1, 13)); ax.set_xticklabels(MONTHS, fontsize=8); ax.grid(axis="y")
    ax.set_title("New loyalty members by month (2025)")
    save(fig, "preview_5_customers.png")


if __name__ == "__main__":
    s, st, p, c, t, f, inv = load()
    page1(s, st, t)
    page2(s)
    page3(s, st, t, f)
    page4(s, inv)
    page5(s, c)
