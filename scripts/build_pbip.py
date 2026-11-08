"""
Generate a Power BI Project (.pbip) for the omnichannel retail model.

    python scripts/build_pbip.py          -> powerbi/OmnichannelRetail.pbip + .SemanticModel + .Report

The semantic model is written in TMDL (Power BI's text model format): every table
with its Power Query source and typed columns, all relationships, dim_date marked as
the date table, Auto date/time off, and every measure from model/measures.dax with its
display folder and format string. The report is created with the five pages from
report/report_spec.md, empty, ready for visuals.

Open powerbi/OmnichannelRetail.pbip in Power BI Desktop, set the DataFolder parameter
to this repo's data/star_schema/ folder, refresh, build the visuals, Save As .pbix.
"""

from __future__ import annotations

import json
import os
import re
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "powerbi")
NAME = "OmnichannelRetail"
MODEL_DIR = os.path.join(OUT, f"{NAME}.SemanticModel")
REPORT_DIR = os.path.join(OUT, f"{NAME}.Report")
DEFAULT_DATA_FOLDER = "C:\\repos\\omnichannel-retail-powerbi\\data\\star_schema\\"


def guid() -> str:
    return str(uuid.uuid4())


# ----------------------------------------------------------------------------- schema

# (column, tmdl dataType, M type, formatString or None, hidden)
TABLES: dict[str, dict] = {
    "dim_date": {
        "file": "dim_date.csv", "gz": False, "date_table": True,
        "columns": [
            ("date_key", "int64", "Int64.Type", "0", True),
            ("date", "dateTime", "type date", "Short Date", False),
            ("year", "int64", "Int64.Type", "0", False),
            ("quarter", "string", "type text", None, False),
            ("year_quarter", "string", "type text", None, False),
            ("month_number", "int64", "Int64.Type", "0", True),
            ("month_name", "string", "type text", None, False),
            ("year_month", "string", "type text", None, False),
            ("week_of_year", "int64", "Int64.Type", "0", False),
            ("day_of_week", "int64", "Int64.Type", "0", True),
            ("day_name", "string", "type text", None, False),
            ("is_weekend", "int64", "Int64.Type", "0", False),
            ("is_holiday", "int64", "Int64.Type", "0", False),
            ("holiday_name", "string", "type text", None, False),
            ("is_month_end", "int64", "Int64.Type", "0", True),
        ],
        "sort_by": {"month_name": "month_number", "day_name": "day_of_week"},
    },
    "dim_month": {
        "derived": True,
        "columns": [
            ("year_month", "string", "type text", None, False),
            ("year", "int64", "Int64.Type", "0", False),
            ("month_number", "int64", "Int64.Type", "0", True),
            ("month_name", "string", "type text", None, False),
        ],
        "sort_by": {"month_name": "month_number"},
    },
    "dim_store": {
        "file": "dim_store.csv", "gz": False,
        "columns": [
            ("store_key", "int64", "Int64.Type", "0", True),
            ("store_code", "string", "type text", None, False),
            ("store_name", "string", "type text", None, False),
            ("channel_type", "string", "type text", None, False),
            ("channel", "string", "type text", None, False),
            ("city", "string", "type text", None, False),
            ("region", "string", "type text", None, False),
            ("store_format", "string", "type text", None, False),
            ("selling_area_sqm", "int64", "Int64.Type", "#,0", False),
            ("open_date", "dateTime", "type date", "Short Date", False),
        ],
    },
    "dim_product": {
        "file": "dim_product.csv", "gz": False,
        "columns": [
            ("product_key", "int64", "Int64.Type", "0", True),
            ("sku", "string", "type text", None, False),
            ("product_name", "string", "type text", None, False),
            ("category", "string", "type text", None, False),
            ("subcategory", "string", "type text", None, False),
            ("season", "string", "type text", None, False),
            ("color", "string", "type text", None, False),
            ("list_price", "int64", "Int64.Type", "#,0", False),
            ("unit_cost", "int64", "Int64.Type", "#,0", False),
            ("price_band", "string", "type text", None, False),
        ],
    },
    "dim_customer": {
        "file": "dim_customer.csv", "gz": False,
        "columns": [
            ("customer_key", "int64", "Int64.Type", "0", True),
            ("customer_id", "string", "type text", None, False),
            ("loyalty_tier", "string", "type text", None, False),
            ("gender", "string", "type text", None, False),
            ("age_band", "string", "type text", None, False),
            ("city", "string", "type text", None, False),
            ("join_date", "dateTime", "type date", "Short Date", False),
        ],
    },
    "fact_sales": {
        "file": "fact_sales.csv.gz", "gz": True, "drop": ["sales_line_id"],
        "columns": [
            ("date_key", "int64", "Int64.Type", "0", True),
            ("store_key", "int64", "Int64.Type", "0", True),
            ("product_key", "int64", "Int64.Type", "0", True),
            ("customer_key", "int64", "Int64.Type", "0", True),
            ("transaction_id", "string", "type text", None, False),
            ("quantity", "int64", "Int64.Type", "#,0", False),
            ("unit_price", "int64", "Int64.Type", "#,0", False),
            ("discount_amount", "int64", "Int64.Type", "#,0", False),
            ("net_sales", "int64", "Int64.Type", "#,0", False),
            ("cost_amount", "int64", "Int64.Type", "#,0", False),
        ],
    },
    "fact_inventory": {
        "file": "fact_inventory.csv.gz", "gz": True,
        "columns": [
            ("date_key", "int64", "Int64.Type", "0", True),
            ("store_key", "int64", "Int64.Type", "0", True),
            ("product_key", "int64", "Int64.Type", "0", True),
            ("stock_on_hand", "int64", "Int64.Type", "#,0", False),
            ("stock_value_at_cost", "int64", "Int64.Type", "#,0", False),
        ],
    },
    "fact_targets": {
        "file": "fact_targets.csv", "gz": False,
        "columns": [
            ("year_month", "string", "type text", None, True),
            ("store_key", "int64", "Int64.Type", "0", True),
            ("sales_target", "int64", "Int64.Type", "#,0", False),
        ],
    },
    "fact_footfall": {
        "file": "fact_footfall.csv", "gz": False,
        "columns": [
            ("date_key", "int64", "Int64.Type", "0", True),
            ("store_key", "int64", "Int64.Type", "0", True),
            ("footfall", "int64", "Int64.Type", "#,0", False),
        ],
    },
}

RELATIONSHIPS = [
    ("fact_sales.date_key", "dim_date.date_key"),
    ("fact_sales.store_key", "dim_store.store_key"),
    ("fact_sales.product_key", "dim_product.product_key"),
    ("fact_sales.customer_key", "dim_customer.customer_key"),
    ("fact_inventory.date_key", "dim_date.date_key"),
    ("fact_inventory.store_key", "dim_store.store_key"),
    ("fact_inventory.product_key", "dim_product.product_key"),
    ("fact_footfall.date_key", "dim_date.date_key"),
    ("fact_footfall.store_key", "dim_store.store_key"),
    ("fact_targets.store_key", "dim_store.store_key"),
    ("dim_date.year_month", "dim_month.year_month"),
    ("fact_targets.year_month", "dim_month.year_month"),
]

PAGES = ["Executive Overview", "Channel Performance", "Store Performance", "Product & Inventory", "Customers & Loyalty"]


# ----------------------------------------------------------------------------- measures

TEXT_MEASURES = {"Selected Period Label", "Last Refresh Label", "Net Sales Short"}
ONE_DECIMAL = {"Weeks of Cover", "Units per Transaction", "Avg Weekly Units", "Avg Basket Value"}
INTEGER_LIKE = {"Target Status"}


def format_for(name: str) -> str | None:
    if name in TEXT_MEASURES:
        return None
    if name.endswith("%"):
        return "0.0%"
    if name in INTEGER_LIKE:
        return "0"
    if name in ONE_DECIMAL:
        return "#,0.0"
    return "#,0"


def parse_measures(path: str) -> list[dict]:
    """Parse model/measures.dax: '// ... Folder: X' comments and 'Name =' blocks."""
    measures, folder = [], ""
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    header = re.compile(r"^(?!VAR\b|RETURN\b)([A-Za-z][A-Za-z0-9 %\-/']*?)\s*=\s*$")
    while i < len(lines):
        line = lines[i]
        m_folder = re.search(r"Folder:\s*(.+?)\s*$", line)
        if line.startswith("//") and m_folder:
            folder = m_folder.group(1)
            i += 1
            continue
        m = header.match(line)
        if m:
            name = m.group(1).strip()
            expr = []
            i += 1
            while i < len(lines) and lines[i].strip() != "" and not header.match(lines[i]):
                if not lines[i].lstrip().startswith("//"):
                    expr.append(lines[i])
                i += 1
            measures.append({"name": name, "expr": "\n".join(expr).strip("\n"), "folder": folder})
            continue
        i += 1
    return measures


# ----------------------------------------------------------------------------- TMDL writers

def m_source(table: str, spec: dict) -> str:
    cols = spec["columns"]
    typed = ", ".join(f'{{"{c}", {mt}}}' for c, _, mt, _, _ in cols if c != "price_band")
    if spec.get("derived"):
        return (
            "let\n"
            "    Source = dim_date,\n"
            '    Months = Table.Distinct(Table.SelectColumns(Source, {"year_month", "year", "month_number", "month_name"})),\n'
            '    Sorted = Table.Sort(Months, {{"year_month", Order.Ascending}})\n'
            "in\n"
            "    Sorted"
        )
    steps = [f'Source = fnLoadCsv("{spec["file"]}", {"true" if spec["gz"] else "false"})',
             f"Typed = Table.TransformColumnTypes(Source, {{{typed}}})"]
    last = "Typed"
    if spec.get("drop"):
        steps.append(f'Slim = Table.RemoveColumns(Typed, {{{", ".join(chr(34) + d + chr(34) for d in spec["drop"])}}})')
        last = "Slim"
    if table == "dim_product":
        steps.append('Banded = Table.AddColumn(Typed, "price_band", each if [list_price] < 250000 then "< 250K" '
                     'else if [list_price] < 450000 then "250K - 449K" else if [list_price] < 650000 then "450K - 649K" else "650K+", type text)')
        last = "Banded"
    body = ",\n".join("    " + s for s in steps)
    return f"let\n{body}\nin\n    {last}"


def indent(text: str, tabs: int) -> str:
    return "\n".join(("\t" * tabs + ln) if ln.strip() else "" for ln in text.splitlines())


def table_tmdl(name: str, spec: dict) -> str:
    out = [f"table {name}", f"\tlineageTag: {guid()}"]
    if spec.get("date_table"):
        out.append("\tdataCategory: Time")
    out.append("")
    for col, dtype, _, fmt, hidden in spec["columns"]:
        out.append(f"\tcolumn {col}")
        out.append(f"\t\tdataType: {dtype}")
        if spec.get("date_table") and col == "date":
            out.append("\t\tisKey")
        if hidden:
            out.append("\t\tisHidden")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {guid()}")
        out.append("\t\tsummarizeBy: none")
        if spec.get("sort_by", {}).get(col):
            out.append(f"\t\tsortByColumn: {spec['sort_by'][col]}")
        out.append(f"\t\tsourceColumn: {col}")
        out.append("")
        if dtype == "dateTime":
            out.insert(len(out) - 1, "\t\tannotation UnderlyingDateTimeDataType = Date")
        out.insert(len(out) - 1, "\t\tannotation SummarizationSetBy = User")
    out.append(f"\tpartition {name} = m")
    out.append("\t\tmode: import")
    out.append("\t\tsource =")
    out.append(indent(m_source(name, spec), 4))
    out.append("")
    out.append("\tannotation PBI_ResultType = Table")
    out.append("")
    return "\n".join(out)


def measures_table_tmdl(measures: list[dict]) -> str:
    out = ["table _Measures", f"\tlineageTag: {guid()}", ""]
    for m in measures:
        name = f"'{m['name']}'" if re.search(r"[^A-Za-z0-9_]", m["name"]) else m["name"]
        expr_lines = m["expr"].splitlines()
        if len(expr_lines) == 1:
            out.append(f"\tmeasure {name} = {expr_lines[0].strip()}")
        else:
            out.append(f"\tmeasure {name} =")
            out.append(indent(m["expr"], 3))
        fmt = format_for(m["name"])
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {guid()}")
        if m["folder"]:
            out.append(f"\t\tdisplayFolder: {m['folder']}")
        out.append("")
    out += ["\tcolumn _", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {guid()}", "\t\tsummarizeBy: none",
            "\t\tsourceColumn: _", "", "\t\tannotation SummarizationSetBy = Automatic", "",
            "\tpartition _Measures = m", "\t\tmode: import", "\t\tsource =",
            "\t\t\t\tlet", '\t\t\t\t    Source = #table(type table [_ = text], {})', "\t\t\t\tin", "\t\t\t\t    Source", "",
            "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)


def relationships_tmdl() -> str:
    out = []
    for frm, to in RELATIONSHIPS:
        out += [f"relationship {guid()}", f"\tfromColumn: {frm}", f"\ttoColumn: {to}", ""]
    return "\n".join(out)


def expressions_tmdl() -> str:
    fn = (
        "(fileName as text, optional gzipped as nullable logical) as table =>\n"
        "let\n"
        "    raw = File.Contents(DataFolder & fileName),\n"
        "    bytes = if gzipped = true then Binary.Decompress(raw, Compression.GZip) else raw,\n"
        "    csv = Csv.Document(bytes, [Delimiter = \",\", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),\n"
        "    promoted = Table.PromoteHeaders(csv, [PromoteAllScalars = true])\n"
        "in\n"
        "    promoted"
    )
    return "\n".join([
        f'expression DataFolder = "{DEFAULT_DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
        f"\tlineageTag: {guid()}",
        "",
        "\tannotation PBI_ResultType = Text",
        "",
        "expression fnLoadCsv =",
        indent(fn, 3),
        f"\tlineageTag: {guid()}",
        "",
        "\tannotation PBI_ResultType = Function",
        "",
    ])


def model_tmdl(tables: list[str]) -> str:
    order = json.dumps(["DataFolder", "fnLoadCsv"] + tables)
    out = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: en-US",
           "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
           f"annotation PBI_QueryOrder = {order}", "", "annotation __PBI_TimeIntelligenceEnabled = 0", "",
           "annotation PBI_ProTooling = [\"DevMode\"]", ""]
    out += [f"ref table {t}" for t in tables]
    out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------------- report

def report_json() -> dict:
    sections = []
    for i, page in enumerate(PAGES):
        sections.append({
            "name": f"ReportSection{i + 1}", "displayName": page, "displayOption": 1, "height": 720.0, "width": 1280.0,
            "config": "{}", "filters": "[]", "ordinal": i, "visualContainers": [],
        })
    config = {
        "version": "5.43", "themeCollection": {"baseTheme": {"name": "CY24SU10", "version": "5.55", "type": 2}},
        "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True,
        "settings": {"useNewFilterPaneExperience": True, "allowChangeFilterTypes": True, "useStylableVisualContainerHeader": True},
    }
    return {
        "config": json.dumps(config), "layoutOptimization": 0,
        "resourcePackages": [{"resourcePackage": {"name": "SharedResources", "type": 2,
                                                  "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": 202}]}}],
        "sections": sections,
    }


def platform(kind: str) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": NAME},
        "config": {"version": "2.0", "logicalId": guid()},
    }


# ----------------------------------------------------------------------------- main

def write(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    measures = parse_measures(os.path.join(ROOT, "model", "measures.dax"))
    tables = list(TABLES) + ["_Measures"]

    # semantic model
    write(os.path.join(MODEL_DIR, "definition.pbism"), json.dumps({"version": "4.0", "settings": {}}, indent=2))
    write(os.path.join(MODEL_DIR, ".platform"), json.dumps(platform("SemanticModel"), indent=2))
    write(os.path.join(MODEL_DIR, "definition", "database.tmdl"), "database\n\tcompatibilityLevel: 1601\n")
    write(os.path.join(MODEL_DIR, "definition", "model.tmdl"), model_tmdl(tables))
    write(os.path.join(MODEL_DIR, "definition", "relationships.tmdl"), relationships_tmdl())
    write(os.path.join(MODEL_DIR, "definition", "expressions.tmdl"), expressions_tmdl())
    for name, spec in TABLES.items():
        write(os.path.join(MODEL_DIR, "definition", "tables", f"{name}.tmdl"), table_tmdl(name, spec))
    write(os.path.join(MODEL_DIR, "definition", "tables", "_Measures.tmdl"), measures_table_tmdl(measures))

    # report
    write(os.path.join(REPORT_DIR, "definition.pbir"), json.dumps({
        "version": "1.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}, "byConnection": None}}, indent=2))
    write(os.path.join(REPORT_DIR, ".platform"), json.dumps(platform("Report"), indent=2))
    write(os.path.join(REPORT_DIR, "report.json"), json.dumps(report_json(), indent=2))

    # project file
    write(os.path.join(OUT, f"{NAME}.pbip"), json.dumps({
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
    write(os.path.join(OUT, ".gitignore"), "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")

    print(f"wrote {os.path.relpath(OUT, ROOT)}/ : {len(TABLES) + 1} tables, {len(RELATIONSHIPS)} relationships, {len(measures)} measures, {len(PAGES)} pages")


if __name__ == "__main__":
    main()
