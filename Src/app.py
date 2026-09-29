import streamlit as st
import pandas as pd
import glob
import os
from sklearn.ensemble import IsolationForest
import plotly.express as px
# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Hybrid Data Analytics & AI Reporting Engine",
    layout="wide"
)

# -----------------------------
# Project Title
# -----------------------------
st.title("📊 Hybrid Data Analytics & AI Reporting Engine")
st.write("Data Analytics Dashboard")

# -----------------------------
# Find Data Folder
# -----------------------------
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder = os.path.join(base_dir, "Data")

# Find any CSV file inside Data folder
csv_files = glob.glob(os.path.join(data_folder, "*.csv"))

# -----------------------------
# Check CSV
# -----------------------------
if not csv_files:
    st.error("❌ CSV file not found in Data folder.")
    st.info("Please keep your CSV file inside the Data folder.")
    st.stop()

# -----------------------------
# Load CSV
# -----------------------------
file_path = csv_files[0]
df = pd.read_csv(file_path)

st.success("✅ Dataset loaded successfully!")

# -----------------------------
# Dataset Information
# -----------------------------
st.subheader("📋 Dataset Preview")
st.dataframe(df.head(10), use_container_width=True)

# -----------------------------
# Region Filter
# -----------------------------

if "region" in df.columns:
    regions = df["region"].dropna().unique().tolist()

    selected_region = st.selectbox(
        "Select Region",
        ["All"] + regions
    )

    if selected_region != "All":
        df = df[df["region"] == selected_region]

 # Product Filter

if "product" in df.columns:
    products = df["product"].dropna().unique().tolist()

    selected_product = st.selectbox(
        "Select Product",
        ["All"] + products
    )

    if selected_product != "All":
        df = df[df["product"] == selected_product]

# Date Filter

if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"])

    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()

    selected_dates = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates

        df = df[
            (df["Date"].dt.date >= start_date) &
            (df["Date"].dt.date <= end_date)
        ]
# -----------------------------
# Numeric Columns
# -----------------------------
numeric_columns = df.select_dtypes(include="number").columns.tolist()

# -----------------------------
# Find Sales Column
# -----------------------------
sales_col = next(
    (col for col in df.columns if "sales" in col.lower()),
    None
)

# -----------------------------
# Find Profit Column
# -----------------------------
profit_col = next(
    (col for col in df.columns if "profit" in col.lower()),
    None
)

# -----------------------------
# Key Metrics
# -----------------------------
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    if sales_col:
        total_sales = df[sales_col].sum()
        st.metric("Total Sales", f"{total_sales:,.2f}")
    else:
        st.metric("Total Sales", "N/A")

with col2:
    if profit_col:
        total_profit = df[profit_col].sum()
        st.metric("Total Profit", f"{total_profit:,.2f}")
    else:
        st.metric("Total Profit", "N/A")

with col3:
    if sales_col:
        average_sales = df[sales_col].mean()
        st.metric("Average Sales", f"{average_sales:,.2f}")
    else:
        st.metric("Average Sales", "N/A")

# -----------------------------
# Data Visualization
# -----------------------------
st.subheader("📈 Data Visualization")

if sales_col:
    st.write("Sales Chart")
    st.line_chart(df[sales_col])

if profit_col:
    st.write("Profit Chart")
    st.line_chart(df[profit_col])

# -----------------------------
# Dataset Statistics
# -----------------------------
st.subheader("📊 Dataset Statistics")

if numeric_columns:
    st.dataframe(
        df[numeric_columns].describe(),
        use_container_width=True
    )
else:
    st.info("No numeric columns found in the dataset.")

# -----------------------------
# Basic AI-style Insights
# -----------------------------
st.subheader("🤖 Basic AI-Style Insight")

if sales_col:
    highest_sales = df[sales_col].max()
    lowest_sales = df[sales_col].min()

    st.write(
        f"• Highest sales value: **{highest_sales:,.2f}**"
    )

    st.write(
        f"• Lowest sales value: **{lowest_sales:,.2f}**"
    )

if profit_col:
    highest_profit = df[profit_col].max()
    lowest_profit = df[profit_col].min()

    st.write(
        f"• Highest profit value: **{highest_profit:,.2f}**"
    )

    st.write(
        f"• Lowest profit value: **{lowest_profit:,.2f}**"
    )

st.success("🎉 Dashboard analysis completed!")



# -----------------------------
# AI-Style Business Report
# -----------------------------

st.header("🤖 AI Business Report")

report = []

if sales_col:
    report.append(
        f"Total sales are {df[sales_col].sum():,.2f}. "
        f"The highest sales value is {df[sales_col].max():,.2f}, "
        f"while the lowest sales value is {df[sales_col].min():,.2f}."
    )

if profit_col:
    report.append(
        f"Total profit is {df[profit_col].sum():,.2f}. "
        f"The highest profit value is {df[profit_col].max():,.2f}, "
        f"while the lowest profit value is {df[profit_col].min():,.2f}."
    )

if sales_col and profit_col:
    report.append(
        "The dashboard compares sales and profit to provide "
        "a quick overview of business performance."
    )

for sentence in report:
    st.write("• " + sentence)

# -----------------------------
# Download AI Business Report
# -----------------------------

from docx import Document
from reportlab.pdfgen import canvas
from io import BytesIO

def create_docx_report():
    doc = Document()

    doc.add_heading("Hybrid Data Analytics & AI Reporting Engine", level=1)
    doc.add_heading("AI Business Report", level=2)

    if sales_col:
        doc.add_paragraph(
            f"Total Sales: {df[sales_col].sum():,.2f}"
        )
        doc.add_paragraph(
            f"Highest Sales: {df[sales_col].max():,.2f}"
        )
        doc.add_paragraph(
            f"Lowest Sales: {df[sales_col].min():,.2f}"
        )
        doc.add_paragraph(
            f"Average Sales: {df[sales_col].mean():,.2f}"
        )

    if profit_col:
        doc.add_paragraph(
            f"Total Profit: {df[profit_col].sum():,.2f}"
        )
        doc.add_paragraph(
            f"Highest Profit: {df[profit_col].max():,.2f}"
        )
        doc.add_paragraph(
            f"Lowest Profit: {df[profit_col].min():,.2f}"
        )

    output = BytesIO()
    doc.save(output)
    output.seek(0)

    return output

report_file = create_docx_report()

st.download_button(
    label="📄 Download AI Report (DOCX)",
    data=report_file,
    file_name="AI_Business_Report.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

from io import BytesIO

def create_pdf_report():
    output = BytesIO()
    pdf = canvas.Canvas(output)

    pdf.setTitle("AI Business Report")

    pdf.drawString(50, 800, "Hybrid Data Analytics & AI Reporting Engine")
    pdf.drawString(50, 775, "AI Business Report")

    pdf.drawString(50, 740, f"Total Sales: {total_sales}")
    pdf.drawString(50, 720, f"Total Profit: {total_profit}")
    pdf.drawString(50, 700, f"Average Sales: {average_sales}")

    pdf.drawString(50, 665, f"Highest Sales: {highest_sales}")
    pdf.drawString(50, 645, f"Lowest Sales: {lowest_sales}")

    pdf.drawString(50, 610, f"Highest Profit: {highest_profit}")
    pdf.drawString(50, 590, f"Lowest Profit: {lowest_profit}")

    pdf.save()
    output.seek(0)

    return output


pdf_file = create_pdf_report()

st.download_button(
    label="📕 Download AI Report (PDF)",
    data=pdf_file,
    file_name="AI_Business_Report.pdf",
    mime="application/pdf"
)

# ---------------- SMART AI BUSINESS INSIGHTS ----------------

st.subheader("🤖 AI Business Insights")

# Sales Insight
if total_sales > average_sales:
    st.success("📈 Sales performance is strong because total sales are above the average sales value.")
else:
    st.info("📊 Sales performance can be improved because total sales are below the average sales value.")

# Profit Insight
if total_profit > 0:
    st.success("💰 The business is generating positive profit.")
else:
    st.warning("⚠️ The business is currently showing a negative profit.")

# Sales Range Insight
sales_range = highest_sales - lowest_sales

if sales_range > average_sales:
    st.info("📊 Sales values show a significant variation across the dataset.")
else:
    st.info("📊 Sales values are relatively consistent across the dataset.")

# Recommendation
st.markdown("### 💡 AI Recommendation")

if total_profit > 0 and highest_sales > average_sales:
    st.write(
        "Focus on maintaining high-performing sales areas and improving "
        "low-performing sales values to increase overall profitability."
    )
else:
    st.write(
        "Review low-performing sales and profit values and identify "
        "areas where business performance can be improved."
    )
# ---------------- ANOMALY DETECTION ----------------

st.subheader("🔍 AI Anomaly Detection")

numeric_columns = df.select_dtypes(include="number").columns

if len(numeric_columns) > 0:

    anomaly_column = st.selectbox(
        "Select a numeric column:",
        numeric_columns
    )

    model = IsolationForest(
        contamination=0.05,
        random_state=42
    )

    df["Anomaly"] = model.fit_predict(
        df[[anomaly_column]]
    )

    anomaly_count = (df["Anomaly"] == -1).sum()

    st.metric("Anomalies Detected", anomaly_count)

    if anomaly_count > 0:
        st.warning(
            f"⚠️ {anomaly_count} unusual values detected in {anomaly_column}."
        )

        st.dataframe(
            df[df["Anomaly"] == -1]
        )
    else:
        st.success("✅ No unusual values detected.")

# ---------------- AI ANOMALY SUMMARY ----------------

st.markdown("### 🤖 AI Anomaly Summary")

if anomaly_count > 0:
    st.write(
        f"The AI model detected {anomaly_count} unusual values "
        f"in the selected {anomaly_column} column."
    )

    st.info(
        "💡 Recommendation: Review these unusual records to identify "
        "possible data-entry errors, unusual business activity, or "
        "important changes in performance."
    )
else:
    st.success(
        "✅ No unusual values were detected in the selected column."
    )

# BUSINESS DASHBOARD
# ============================================================

st.markdown("---")
st.markdown("## 📊 Bussiness Dashboard")

st.write("### Sales & Profit Overview")

# Find Sales and Profit columns
sales_col = None
profit_col = None

for col in df.columns:
    col_lower = col.lower()

    if "sales" in col_lower or "revenue" in col_lower:
        sales_col = col

    if "profit" in col_lower:
        profit_col = col

# Sales vs Profit chart
if sales_col and profit_col:

    dashboard_data = pd.DataFrame({
        "Metric": ["Total Sales", "Total Profit"],
        "Value": [
            df[sales_col].sum(),
            df[profit_col].sum()
        ]
    })

    fig_dashboard = px.bar(
        dashboard_data,
        x="Metric",
        y="Value",
        title="Total Sales vs Total Profit",
        text="Value"
    )

    st.plotly_chart(fig_dashboard, use_container_width=True)

else:
    st.warning("Sales or Profit column was not found in the dataset.") 

# ============================================================
# CATEGORY PERFORMANCE
# ============================================================

st.markdown("---")
st.markdown("## 🌍 Category Performance")
st.write("Available Columns:", list)

st.write("Available Columns:", df.columns.tolist())

category_col = None

for col in df.columns:
    col_lower = col.lower()

    if "category" in col_lower or "product" in col_lower:
        category_col = col

        break

if category_col and sales_col:

    category_data = (
        df.groupby(category_col)[sales_col]
        .sum()
        .reset_index()
    )

    fig_category = px.bar(
        category_data,
        x=category_col,
        y=sales_col,
        title="Sales by Category",
        text=sales_col
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )

else:
    st.info("Category column was not found in the dataset.")   

# ============================================================
# AI BUSINESS INSIGHTS
# ============================================================

st.markdown("---")
st.markdown("## 🤖 AI Business Insights")

if category_col and sales_col:

    best_category = category_data.loc[
        category_data[sales_col].idxmax(),
        category_col
    ]

    best_sales = category_data[sales_col].max()

    total_sales = category_data[sales_col].sum()

    best_percentage = (best_sales / total_sales) * 100

    st.success(
        f"🏆 *Top Performing Category:* {best_category}"
    )

    st.info(
        f"📈 *Business Insight:* {best_category} generated "
        f"{best_sales:,.2f} in sales, contributing approximately "
        f"{best_percentage:.1f}% of total category sales."
    )

    st.write(
        "💡 *Recommendation:* Focus on the top-performing "
        "category while monitoring the performance of other categories "
        "to identify growth opportunities."
    )

else:
    st.warning("AI insights cannot be generated because category or sales data is missing.")    

# ============================================================
# TREND ANALYSIS
# ============================================================

st.markdown("---")
st.markdown("## 📈 Sales & Profit Trend Analysis")

if "Date" in df.columns and sales_col:

    trend_data = df.copy()

    trend_data["Date"] = pd.to_datetime(
        trend_data["Date"],
        errors="coerce"
    )

    trend_data = trend_data.dropna(subset=["Date"])

    trend_data = (
        trend_data
        .groupby("Date")[[sales_col, "Profit"]]
        .sum()
        .reset_index()
        .sort_values("Date")
    )

    fig_trend = px.line(
        trend_data,
        x="Date",
        y=[sales_col, "Profit"],
        markers=True,
        title="Sales and Profit Trend"
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )

else:
    st.info("Date, Sales or Profit column was not found.")

# ============================================================
# TREND-BASED AI INSIGHTS
# ============================================================

st.markdown("---")
st.markdown("## 🤖 Trend-Based AI Insights")

if len(trend_data) >= 2:

    first_sales = trend_data[sales_col].iloc[0]
    last_sales = trend_data[sales_col].iloc[-1]

    first_profit = trend_data["Profit"].iloc[0]
    last_profit = trend_data["Profit"].iloc[-1]

    if last_sales > first_sales:
        sales_insight = "📈 Sales are showing an increasing trend."
    elif last_sales < first_sales:
        sales_insight = "📉 Sales are showing a decreasing trend."
    else:
        sales_insight = "➡️ Sales are relatively stable."

    if last_profit > first_profit:
        profit_insight = "📈 Profit is showing an increasing trend."
    elif last_profit < first_profit:
        profit_insight = "📉 Profit is showing a decreasing trend."
    else:
        profit_insight = "➡️ Profit is relatively stable."

    st.info(sales_insight)
    st.info(profit_insight)

    st.success(
        "💡 Business Recommendation: Monitor the latest sales and "
        "profit performance regularly to identify growth opportunities "
        "and potential business risks."
    )

else:
    st.warning("Not enough data available for trend-based insights.")

# ============================================================
# ANOMALY INSIGHTS
# ============================================================

st.markdown("---")
st.markdown("## ⚠️ Anomaly Insights")

if "Anomaly" in df.columns:

    anomaly_count = (df["Anomaly"] == -1).sum()

    st.metric(
        "Detected Anomalies",
        anomaly_count
    )

    if anomaly_count > 0:

        anomaly_data = df[df["Anomaly"] == -1]

        st.warning(
            f"⚠️ {anomaly_count} unusual records were detected "
            "in the dataset."
        )

        st.write("### 🔍 Unusual Records")

        st.dataframe(
            anomaly_data,
            use_container_width=True
        )

        st.info(
            "💡 Business Insight: These unusual records should be "
            "reviewed to understand whether they represent unusual "
            "business activity, data errors, or exceptional transactions."
        )

    else:
        st.success(
            "✅ No unusual records were detected in the dataset."
        )

else:
    st.info(
        "Anomaly column was not found in the dataset."
    )

st.info(
    "Anomaly column was not found in the dataset."
)

# Smart Business Recommendations

st.markdown("---")
st.header("💡 Smart Business Recommendations")

if "df" in locals() and not df.empty:

    sales_column = locals().get("sales_col")
    profit_column = locals().get("profit_col")

    if sales_column in df.columns and profit_column in df.columns:

        total_sales = df[sales_column].sum()
        total_profit = df[profit_column].sum()

        if total_sales > 0:

            profit_margin = (total_profit / total_sales) * 100

            st.metric(
                "Profit Margin",
                f"{profit_margin:.2f}%"
            )

            if profit_margin < 10:
                st.warning(
                    "Recommendation: Review business expenses "
                    "and improve profit margins."
                )

            else:
                st.success(
                    "Recommendation: Maintain the current "
                    "profit performance and monitor trends."
                )

            if "region" in df.columns:

                region_sales = df.groupby("region")[sales_column].sum()

                best_region = region_sales.idxmax()

                st.info(
                    f"Top Performing Region: {best_region}. "
                    "Study its sales performance for business planning."
                )

        else:
            st.info("Sales data is zero. More data is needed.")

    else:
        st.info("Sales or Profit column is not available.")

else:
    st.info("Please upload a dataset to see recommendations.")