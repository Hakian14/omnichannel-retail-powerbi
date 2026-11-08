// =============================================================================
// Power Query (M) - load the star schema from data/star_schema/
// -----------------------------------------------------------------------------
// 1. Create a parameter  DataFolder  (Text)  pointing at the star_schema folder,
//    e.g.  C:\repos\omnichannel-retail-powerbi\data\star_schema\
// 2. Paste each query below into a blank query (Home > New Source > Blank Query
//    > Advanced Editor), name it as indicated.
// 3. The two gzipped facts are decompressed in-query with Binary.Decompress.
// =============================================================================


// ---- fnLoadCsv (function) ---------------------------------------------------
// Loads a CSV, optionally gzipped, and promotes headers.
(fileName as text, optional gzipped as nullable logical) as table =>
let
    raw      = File.Contents(DataFolder & fileName),
    bytes    = if gzipped = true then Binary.Decompress(raw, Compression.GZip) else raw,
    csv      = Csv.Document(bytes, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    promoted = Table.PromoteHeaders(csv, [PromoteAllScalars = true])
in
    promoted


// ---- dim_date ---------------------------------------------------------------
let
    Source = fnLoadCsv("dim_date.csv", false),
    Typed  = Table.TransformColumnTypes(Source, {
        {"date_key", Int64.Type}, {"date", type date}, {"year", Int64.Type}, {"quarter", type text},
        {"year_quarter", type text}, {"month_number", Int64.Type}, {"month_name", type text},
        {"year_month", type text}, {"week_of_year", Int64.Type}, {"day_of_week", Int64.Type},
        {"day_name", type text}, {"is_weekend", Int64.Type}, {"is_holiday", Int64.Type},
        {"holiday_name", type text}, {"is_month_end", Int64.Type}})
in
    Typed


// ---- dim_month (bridge for monthly targets) --------------------------------
let
    Source  = dim_date,
    Months  = Table.Distinct(Table.SelectColumns(Source, {"year_month", "year", "month_number", "month_name"})),
    Sorted  = Table.Sort(Months, {{"year_month", Order.Ascending}})
in
    Sorted


// ---- dim_store --------------------------------------------------------------
let
    Source = fnLoadCsv("dim_store.csv", false),
    Typed  = Table.TransformColumnTypes(Source, {
        {"store_key", Int64.Type}, {"store_code", type text}, {"store_name", type text},
        {"channel_type", type text}, {"channel", type text}, {"city", type text}, {"region", type text},
        {"store_format", type text}, {"selling_area_sqm", Int64.Type}, {"open_date", type date}})
in
    Typed


// ---- dim_product ------------------------------------------------------------
let
    Source = fnLoadCsv("dim_product.csv", false),
    Typed  = Table.TransformColumnTypes(Source, {
        {"product_key", Int64.Type}, {"sku", type text}, {"product_name", type text}, {"category", type text},
        {"subcategory", type text}, {"season", type text}, {"color", type text},
        {"list_price", Int64.Type}, {"unit_cost", Int64.Type}}),
    // Price band used as a slicer on the Product page
    Banded = Table.AddColumn(Typed, "price_band", each
        if [list_price] < 250000 then "< 250K"
        else if [list_price] < 450000 then "250K - 449K"
        else if [list_price] < 650000 then "450K - 649K"
        else "650K+", type text)
in
    Banded


// ---- dim_customer -----------------------------------------------------------
let
    Source = fnLoadCsv("dim_customer.csv", false),
    Typed  = Table.TransformColumnTypes(Source, {
        {"customer_key", Int64.Type}, {"customer_id", type text}, {"loyalty_tier", type text},
        {"gender", type text}, {"age_band", type text}, {"city", type text}, {"join_date", type date}})
in
    Typed


// ---- fact_sales -------------------------------------------------------------
let
    Source = fnLoadCsv("fact_sales.csv.gz", true),
    Typed  = Table.TransformColumnTypes(Source, {
        {"sales_line_id", Int64.Type}, {"date_key", Int64.Type}, {"store_key", Int64.Type},
        {"product_key", Int64.Type}, {"customer_key", Int64.Type}, {"transaction_id", type text},
        {"quantity", Int64.Type}, {"unit_price", Int64.Type}, {"discount_amount", Int64.Type},
        {"net_sales", Int64.Type}, {"cost_amount", Int64.Type}}),
    // sales_line_id is not needed for any measure - dropping it removes the
    // highest-cardinality column in the model.
    Slim   = Table.RemoveColumns(Typed, {"sales_line_id"})
in
    Slim


// ---- fact_inventory ---------------------------------------------------------
let
    Source = fnLoadCsv("fact_inventory.csv.gz", true),
    Typed  = Table.TransformColumnTypes(Source, {
        {"date_key", Int64.Type}, {"store_key", Int64.Type}, {"product_key", Int64.Type},
        {"stock_on_hand", Int64.Type}, {"stock_value_at_cost", Int64.Type}})
in
    Typed


// ---- fact_targets -----------------------------------------------------------
let
    Source = fnLoadCsv("fact_targets.csv", false),
    Typed  = Table.TransformColumnTypes(Source, {
        {"year_month", type text}, {"store_key", Int64.Type}, {"sales_target", Int64.Type}})
in
    Typed


// ---- fact_footfall ----------------------------------------------------------
let
    Source = fnLoadCsv("fact_footfall.csv", false),
    Typed  = Table.TransformColumnTypes(Source, {
        {"date_key", Int64.Type}, {"store_key", Int64.Type}, {"footfall", Int64.Type}})
in
    Typed


// ---- _Measures (empty table to host measures) -------------------------------
let
    Source = #table({"_"}, {{null}})
in
    Source
