import glob
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from engine_helpers import (
    build_docx_report,
    build_pdf_report,
    find_col,
    fmt,
    health_check,
)
from engine_insights import show_insights, show_performance, show_why_changed
from engine_predict import show_anomaly, show_forecast, show_whatif

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

    st.plotly_chart(
        px.line(
            trend,
            x=date_col,
            y=value_cols,
            markers=True,
            title=f"Sales and Profit Trend ({view_by})"
        )
    )
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

st.download_button(
    label="📄 Download AI Report (DOCX)",
    data=build_docx_report(report_lines),
    file_name="AI_Business_Report.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

st.download_button(
    label="📕 Download AI Report (PDF)",
    data=build_pdf_report(report_lines),
    file_name="AI_Business_Report.pdf",
    mime="application/pdf"
)

# =============================================================
# Analysis sections (the code for these lives in the engine_*.py files)
# =============================================================
product_table, region_table = show_performance(
    df, product_col, region_col, sales_col, profit_col
)

show_insights(
    df, date_col, sales_col, product_col, region_col,
    product_table, region_table, profit_margin, total_sales
)

show_why_changed(df_all, date_col, sales_col, product_col, region_col)

forecast_result = show_forecast(df, date_col, sales_col)

whatif_result = show_whatif(
    sales_col, profit_col, total_sales, total_profit, profit_margin
)

show_anomaly(df, numeric_columns, product_col)

st.success("🎉 Dashboard analysis completed!")
