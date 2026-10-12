import glob
import os
import textwrap
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from docx import Document
from reportlab.pdfgen import canvas

# =============================================================
# Page Configuration & Title
# =============================================================
st.set_page_config(
    page_title="Hybrid Data Analytics & AI Reporting Engine",
    layout="wide"
)

st.title("📊 Hybrid Data Analytics & AI Reporting Engine")
st.write("Data Analytics Dashboard")


# =============================================================
# Helper functions
# =============================================================
def find_col(columns, keywords):
    """Return the first column whose name contains one of the keywords."""
    for keyword in keywords:
        for col in columns:
            if keyword in col.lower():
                return col
    return None


def fmt(value):
    """Format a number for display; None becomes N/A."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.2f}"


def health_check(data, sales, profit, quantity, date):
    """Return (score, issues) describing the quality of the raw data."""
    total_rows = len(data)
    bad_rows = pd.Series(False, index=data.index)

    missing = data.isna()
    duplicates = data.duplicated()
    bad_rows |= missing.any(axis=1)
    bad_rows |= duplicates

    not_numeric = pd.Series(False, index=data.index)
    negative = pd.Series(False, index=data.index)

    for col in [sales, profit, quantity]:
        if col:
            converted = pd.to_numeric(data[col], errors="coerce")
            not_numeric |= converted.isna() & data[col].notna()
            if col != profit:  # negative profit (loss) is valid
                negative |= converted < 0

    invalid_dates = pd.Series(False, index=data.index)
    if date:
        parsed = pd.to_datetime(data[date], errors="coerce")
        invalid_dates = parsed.isna() & data[date].notna()

    bad_rows |= not_numeric | negative | invalid_dates

    issues = {
        "Missing values": int(missing.sum().sum()),
        "Duplicate rows": int(duplicates.sum()),
        "Non-numeric values in number columns": int(not_numeric.sum()),
        "Negative sales / quantity values": int(negative.sum()),
        "Invalid dates": int(invalid_dates.sum()),
    }

    score = 100.0 * (1 - bad_rows.sum() / total_rows) if total_rows else 0.0
    return score, issues


def partial_month_note(month, last_date):
    """Warn when a month is the final month of the data and not fully covered."""
    if (
        last_date is not None
        and not pd.isna(last_date)
        and month == last_date.strftime("%Y-%m")
        and last_date.day < last_date.days_in_month
    ):
        return f" (Note: {month} may be incomplete, data ends on {last_date.date()}.)"
    return ""


def group_table(data, dim, sales, profit):
    """Sales, profit and margin % grouped by a column."""
    value_cols = [c for c in [sales, profit] if c]
    table = data.groupby(dim)[value_cols].sum()
    if sales and profit:
        table["Margin %"] = (
            table[profit] / table[sales].replace(0, float("nan")) * 100
        ).round(2)
    return table.reset_index()


# =============================================================
# Upload / Load dataset
# =============================================================
st.subheader("Upload Your Dataset")

uploaded_file = st.file_uploader(
    "Choose CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        st.success("Dataset uploaded successfully!")

    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        st.stop()

else:
    data_folder = os.path.join(os.getcwd(), "Data")
    csv_files = sorted(glob.glob(os.path.join(data_folder, "*.csv")))

    if not csv_files:
        st.error("Please upload a CSV or Excel dataset.")
        st.stop()

    df_raw = pd.read_csv(csv_files[0])
    st.info("Default dataset loaded successfully!")

if df_raw.empty:
    st.error("The dataset is empty. Please upload a file with data.")
    st.stop()

# =============================================================
# Detect columns (case-insensitive)
# =============================================================
df_raw.columns = df_raw.columns.astype(str).str.strip()
all_cols = df_raw.columns.tolist()
lookup = {col.lower(): col for col in all_cols}

region_col = lookup.get("region")
product_col = lookup.get("product")
date_col = lookup.get("date")
sales_col = find_col(all_cols, ["sales", "revenue"])
profit_col = find_col(all_cols, ["profit"])
quantity_col = find_col(all_cols, ["quantity", "qty"])

# =============================================================
# Dataset Preview
# =============================================================
st.subheader("📋 Dataset Preview")
st.dataframe(df_raw.head(10))

# =============================================================
# Data Health Check (runs on the raw data)
# =============================================================
st.subheader("🩺 Data Health Check")

health_score, health_issues = health_check(
    df_raw, sales_col, profit_col, quantity_col, date_col
)

st.metric("Data Health Score", f"{health_score:.0f}%")
st.caption("Share of rows with no missing, duplicate, invalid or negative values.")

for issue_name, issue_count in health_issues.items():
    if issue_count:
        st.warning(f"{issue_name}: {issue_count}")
    else:
        st.success(f"{issue_name}: 0")

if len(df_raw) < 30:
    st.info(
        "Small dataset: only "
        f"{len(df_raw)} rows. Insights are more reliable with 30+ rows."
    )

# =============================================================
# Clean data for analysis
# =============================================================
df_all = df_raw.copy()

for col in [sales_col, profit_col, quantity_col]:
    if col:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

if sales_col and df_all[sales_col].notna().sum() == 0:
    sales_col = None
if profit_col and df_all[profit_col].notna().sum() == 0:
    profit_col = None

if date_col:
    df_all[date_col] = pd.to_datetime(df_all[date_col], errors="coerce")
    if df_all[date_col].notna().sum() == 0:
        date_col = None

# =============================================================
# Filters
# =============================================================
df = df_all.copy()

if region_col:
    regions = sorted(df[region_col].dropna().astype(str).unique().tolist())
    selected_region = st.selectbox("Select Region", ["All"] + regions)

    if selected_region != "All":
        df = df[df[region_col].astype(str) == selected_region]

if product_col:
    products = sorted(df[product_col].dropna().astype(str).unique().tolist())
    selected_product = st.selectbox("Select Product", ["All"] + products)

    if selected_product != "All":
        df = df[df[product_col].astype(str) == selected_product]

if date_col:
    valid_dates = df[date_col].dropna()

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        selected_dates = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
            df = df[
                df[date_col].notna()
                & (df[date_col].dt.date >= start_date)
                & (df[date_col].dt.date <= end_date)
            ]

if df.empty:
    st.warning(
        "No data found for the selected filters. "
        "Please change your filters."
    )
    st.stop()

# =============================================================
# Key numbers (calculated once, used everywhere below)
# =============================================================
total_sales = average_sales = highest_sales = lowest_sales = None
total_profit = highest_profit = lowest_profit = profit_margin = None

if sales_col:
    total_sales = float(df[sales_col].sum())
    average_sales = float(df[sales_col].mean())
    highest_sales = float(df[sales_col].max())
    lowest_sales = float(df[sales_col].min())

if profit_col:
    total_profit = float(df[profit_col].sum())
    highest_profit = float(df[profit_col].max())
    lowest_profit = float(df[profit_col].min())

if total_sales and total_profit is not None and total_sales > 0:
    profit_margin = total_profit / total_sales * 100

# =============================================================
# Key Metrics
# =============================================================
st.subheader("📌 Key Metrics")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Sales", fmt(total_sales))
m2.metric("Total Profit", fmt(total_profit))
m3.metric("Average Sales", fmt(average_sales))
m4.metric(
    "Profit Margin",
    f"{profit_margin:.2f}%" if profit_margin is not None else "N/A"
)

# =============================================================
# Data Visualization (by date, not by row number)
# =============================================================
st.subheader("📈 Data Visualization")

value_cols = [c for c in [sales_col, profit_col] if c]

if date_col and value_cols:
    view_by = st.selectbox("View trend by", ["Daily", "Weekly", "Monthly"])
    freq = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}[view_by]

    trend = (
        df.dropna(subset=[date_col])
        .groupby(pd.Grouper(key=date_col, freq=freq))[value_cols]
        .sum()
        .reset_index()
    )

    fig_trend = px.line(
        trend,
        x=date_col,
        y=value_cols,
        markers=True,
        title=f"Sales and Profit Trend ({view_by})"
    )
    st.plotly_chart(fig_trend)
elif value_cols:
    st.info("No valid Date column found, so the trend chart is skipped.")
else:
    st.info("No Sales or Profit column found for charts.")

# =============================================================
# Dataset Statistics
# =============================================================
st.subheader("📊 Dataset Statistics")

numeric_columns = df.select_dtypes(include="number").columns.tolist()

if numeric_columns:
    st.dataframe(df[numeric_columns].describe())
else:
    st.info("No numeric columns found in the dataset.")

# =============================================================
# AI Business Report (text) + downloads
# =============================================================
st.header("🤖 AI Business Report")

report_lines = []

if sales_col:
    report_lines.append(
        f"Total sales are {total_sales:,.2f}. "
        f"The highest single sale is {highest_sales:,.2f} and "
        f"the lowest is {lowest_sales:,.2f}."
    )

if profit_col:
    report_lines.append(
        f"Total profit is {total_profit:,.2f}. "
        f"The highest single profit is {highest_profit:,.2f} and "
        f"the lowest is {lowest_profit:,.2f}."
    )

if profit_margin is not None:
    report_lines.append(f"The overall profit margin is {profit_margin:.2f}%.")

report_lines.append(f"Data health score of the uploaded data: {health_score:.0f}%.")

for sentence in report_lines:
    st.write("• " + sentence)


def create_docx_report():
    doc = Document()
    doc.add_heading("Hybrid Data Analytics & AI Reporting Engine", level=1)
    doc.add_heading("AI Business Report", level=2)
    for line in report_lines:
        doc.add_paragraph(line)
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output


def create_pdf_report():
    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.setTitle("AI Business Report")
    pdf.drawString(50, 800, "Hybrid Data Analytics & AI Reporting Engine")
    pdf.drawString(50, 775, "AI Business Report")

    y = 740
    for line in report_lines:
        for part in textwrap.wrap(line, 90) or [""]:
            if y < 60:
                pdf.showPage()
                y = 800
            pdf.drawString(50, y, part)
            y -= 18
        y -= 8

    pdf.save()
    output.seek(0)
    return output


st.download_button(
    label="📄 Download AI Report (DOCX)",
    data=create_docx_report(),
    file_name="AI_Business_Report.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

st.download_button(
    label="📕 Download AI Report (PDF)",
    data=create_pdf_report(),
    file_name="AI_Business_Report.pdf",
    mime="application/pdf"
)

# =============================================================
# Performance by Product and Region
# =============================================================
st.markdown("---")
st.markdown("## 📊 Business Dashboard")

product_table = None
region_table = None

if sales_col and product_col:
    product_table = group_table(df, product_col, sales_col, profit_col)
    st.write("### Performance by Product")
    st.plotly_chart(
        px.bar(product_table, x=product_col, y=sales_col,
               title="Sales by Product", text=sales_col)
    )
    st.dataframe(product_table)

if sales_col and region_col:
    region_table = group_table(df, region_col, sales_col, profit_col)
    st.write("### Performance by Region")
    st.plotly_chart(
        px.bar(region_table, x=region_col, y=sales_col,
               title="Sales by Region", text=sales_col)
    )
    st.dataframe(region_table)

if product_table is None and region_table is None:
    st.info("Product/Region and Sales columns are needed for this section.")

# =============================================================
# AI Business Insights & Recommendations (rule-based)
# =============================================================
st.markdown("---")
st.markdown("## 🤖 AI Business Insights")

insight_count = 0

if profit_margin is not None:
    if profit_margin >= 20:
        st.success(f"💰 Healthy profit margin of {profit_margin:.1f}%.")
    elif profit_margin >= 10:
        st.info(f"💰 Moderate profit margin of {profit_margin:.1f}%.")
    elif profit_margin >= 0:
        st.warning(f"⚠️ Low profit margin of {profit_margin:.1f}%. Review costs.")
    else:
        st.error(f"🚨 The business is making a loss (margin {profit_margin:.1f}%).")
    insight_count += 1

if product_table is not None and len(product_table) >= 2 and total_sales:
    top = product_table.loc[product_table[sales_col].idxmax()]
    share = top[sales_col] / total_sales * 100
    st.info(
        f"🏆 Top product by sales: {top[product_col]} "
        f"({share:.1f}% of total sales)."
    )
    insight_count += 1

    if "Margin %" in product_table.columns and product_table["Margin %"].notna().any():
        low = product_table.loc[product_table["Margin %"].idxmin()]
        high = product_table.loc[product_table["Margin %"].idxmax()]
        st.info(
            f"📉 Lowest margin product: {low[product_col]} "
            f"({low['Margin %']:.1f}%). "
            f"Highest margin: {high[product_col]} ({high['Margin %']:.1f}%)."
        )
        insight_count += 1

if region_table is not None and len(region_table) >= 2:
    best_region = region_table.loc[region_table[sales_col].idxmax()]
    worst_region = region_table.loc[region_table[sales_col].idxmin()]
    st.info(
        f"🌍 Best region: {best_region[region_col]} | "
        f"Weakest region: {worst_region[region_col]}."
    )
    insight_count += 1

if date_col and sales_col:
    monthly = (
        df.dropna(subset=[date_col])
        .assign(Month=lambda d: d[date_col].dt.strftime("%Y-%m"))
        .groupby("Month")[sales_col].sum()
    )
    if len(monthly) >= 2 and monthly.iloc[-2] != 0:
        change = (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100
        icon = "📈" if change >= 0 else "📉"
        word = "increased" if change >= 0 else "decreased"
        st.info(
            f"{icon} Sales {word} by {abs(change):.1f}% "
            f"in {monthly.index[-1]} compared to {monthly.index[-2]}."
            + partial_month_note(monthly.index[-1], df[date_col].max())
        )
        insight_count += 1

if insight_count == 0:
    st.info("Not enough data to generate insights.")

st.markdown("### 💡 Recommendations")

recommendations = []
if profit_margin is not None and profit_margin < 10:
    recommendations.append(
        "Overall margin is low: review discounts and costs before pushing more volume."
    )
if (
    product_table is not None
    and "Margin %" in product_table.columns
    and product_table["Margin %"].notna().any()
    and len(product_table) >= 2
):
    low = product_table.loc[product_table["Margin %"].idxmin()]
    recommendations.append(
        f"Review pricing or costs of {low[product_col]}, "
        "it earns the least profit per unit of sales."
    )
if region_table is not None and len(region_table) >= 2:
    worst_region = region_table.loc[region_table[sales_col].idxmin()]
    recommendations.append(
        f"Investigate why {worst_region[region_col]} has the lowest sales "
        "(stock, demand or team coverage)."
    )

if recommendations:
    for rec in recommendations:
        st.write("• " + rec)
else:
    st.write("• Keep monitoring sales and margin regularly.")

# =============================================================
# Why did it change? (uses the full dataset, ignores filters)
# =============================================================
st.markdown("---")
st.markdown("## 🔎 Why Did Sales Change?")

if date_col and sales_col:
    base = df_all.dropna(subset=[date_col]).copy()
    base["Month"] = base[date_col].dt.strftime("%Y-%m")
    months = sorted(base["Month"].unique().tolist())
    dims = [c for c in [product_col, region_col] if c]

    if len(months) >= 2 and dims:
        st.caption("This section uses the full dataset and ignores the filters above.")

        dim = st.selectbox("Explain change by", dims)
        prev_month = st.selectbox("Previous month", months, index=len(months) - 2)
        curr_month = st.selectbox("Current month", months, index=len(months) - 1)

        if prev_month == curr_month:
            st.info("Please select two different months.")
        else:
            prev = base[base["Month"] == prev_month].groupby(dim)[sales_col].sum()
            curr = base[base["Month"] == curr_month].groupby(dim)[sales_col].sum()

            comp = pd.DataFrame({"Previous": prev, "Current": curr}).fillna(0)
            comp["Change"] = comp["Current"] - comp["Previous"]
            comp["Change %"] = (
                comp["Change"] / comp["Previous"].replace(0, float("nan")) * 100
            ).round(1)
            comp = comp.sort_values("Change")

            total_prev = float(comp["Previous"].sum())
            total_curr = float(comp["Current"].sum())
            total_change = total_curr - total_prev
            worst = comp.index[0]
            best = comp.index[-1]

            if total_prev > 0:
                pct_text = f" ({total_change / total_prev * 100:+.1f}%)"
            else:
                pct_text = ""

            verb = "rose" if total_change >= 0 else "fell"
            summary = (
                f"Sales {verb} by {abs(total_change):,.0f}{pct_text} "
                f"from {prev_month} to {curr_month}. "
            )
            if comp["Change"].iloc[0] < 0:
                summary += (
                    f"Biggest drop: {worst} ({comp['Change'].iloc[0]:,.0f}). "
                )
                if total_change < 0 and abs(comp["Change"].iloc[0]) <= abs(total_change):
                    share = comp["Change"].iloc[0] / total_change * 100
                    summary += f"It alone accounts for {share:.0f}% of the net fall. "
                else:
                    summary += "Gains elsewhere offset part of this drop"