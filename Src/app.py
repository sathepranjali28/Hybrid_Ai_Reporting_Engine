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
"""Small helper functions used by app.py (no Streamlit code in this file)."""
import textwrap
from io import BytesIO

import pandas as pd
from docx import Document
from reportlab.pdfgen import canvas


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


def build_docx_report(report_lines):
    """Return the business report as an in-memory Word file."""
    doc = Document()
    doc.add_heading("Hybrid Data Analytics & AI Reporting Engine", level=1)
    doc.add_heading("AI Business Report", level=2)
    for line in report_lines:
        doc.add_paragraph(line)
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output


def build_pdf_report(report_lines):
    """Return the business report as an in-memory PDF file."""
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
"""Business dashboard, insights and 'Why did sales change?' sections."""
import pandas as pd
import plotly.express as px
import streamlit as st

from engine_helpers import group_table, partial_month_note


def show_performance(df, product_col, region_col, sales_col, profit_col):
    """Charts and tables by product and region. Returns (product_table, region_table)."""
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

    return product_table, region_table


def show_insights(df, date_col, sales_col, product_col, region_col,
                  product_table, region_table, profit_margin, total_sales):
    """Rule-based insights and recommendations."""
    st.markdown("---")
    st.markdown("## 🤖 AI Business Insights")

    insight_count = 0
    has_margin_table = (
        product_table is not None
        and "Margin %" in product_table.columns
        and product_table["Margin %"].notna().any()
    )

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

        if has_margin_table:
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
    if has_margin_table and len(product_table) >= 2:
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


def show_why_changed(df_all, date_col, sales_col, product_col, region_col):
    """Compare two months and rank the products/regions behind the change."""
    st.markdown("---")
    st.markdown("## 🔎 Why Did Sales Change?")

    if not (date_col and sales_col):
        st.info("A valid Date column and a Sales column are needed for this section.")
        return

    base = df_all.dropna(subset=[date_col]).copy()
    base["Month"] = base[date_col].dt.strftime("%Y-%m")
    months = sorted(base["Month"].unique().tolist())
    dims = [c for c in [product_col, region_col] if c]

    if len(months) < 2 or not dims:
        st.info("At least two months of data and a Product or Region column are needed.")
        return

    st.caption("This section uses the full dataset and ignores the filters above.")

    dim = st.selectbox("Explain change by", dims)
    prev_month = st.selectbox("Previous month", months, index=len(months) - 2)
    curr_month = st.selectbox("Current month", months, index=len(months) - 1)

    if prev_month == curr_month:
        st.info("Please select two different months.")
        return

    prev = base[base["Month"] == prev_month].groupby(dim)[sales_col].sum()
    curr = base[base["Month"] == curr_month].groupby(dim)[sales_col].sum()

    comp = pd.DataFrame({"Previous": prev, "Current": curr}).fillna(0)
    comp["Change"] = comp["Current"] - comp["Previous"]
    comp["Change %"] = (
        comp["Change"] / comp["Previous"].replace(0, float("nan")) * 100
    ).round(1)
    comp = comp.sort_values("Change")

    total_prev = float(comp["Previous"].sum())
    total_change = float(comp["Current"].sum()) - total_prev
    worst = comp.index[0]
    best = comp.index[-1]
    biggest_drop = comp["Change"].iloc[0]
    biggest_gain = comp["Change"].iloc[-1]

    pct_text = ""
    if total_prev > 0:
        pct_text = f" ({total_change / total_prev * 100:+.1f}%)"

    verb = "rose" if total_change >= 0 else "fell"
    summary = (
        f"Sales {verb} by {abs(total_change):,.0f}{pct_text} "
        f"from {prev_month} to {curr_month}. "
    )
    if biggest_drop < 0:
        summary += f"Biggest drop: {worst} ({biggest_drop:,.0f}). "
        if total_change < 0 and abs(biggest_drop) <= abs(total_change):
            share = biggest_drop / total_change * 100
            summary += f"It alone accounts for {share:.0f}% of the net fall. "
        else:
            summary += "Gains elsewhere offset part of this drop. "
    if biggest_gain > 0:
        summary += f"Biggest gain: {best} (+{biggest_gain:,.0f})."
    summary += partial_month_note(curr_month, df_all[date_col].max())

    if total_change >= 0:
        st.success(summary)
    else:
        st.warning(summary)

    comp_table = comp.reset_index()
    st.plotly_chart(
        px.bar(comp_table, x=dim, y="Change", title=f"Change in sales by {dim}")
    )
    st.dataframe(comp_table)
    """Sales forecast, what-if simulator and anomaly detection sections."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from engine_helpers import fmt


def show_forecast(df, date_col, sales_col):
    """Straight-line trend forecast on monthly totals. Returns a dict or None."""
    st.markdown("---")
    st.markdown("## 🔮 Sales Forecast")

    if not (date_col and sales_col):
        st.info("A valid Date column and a Sales column are needed for the forecast.")
        return None

    monthly_sales = (
        df.dropna(subset=[date_col])
        .groupby(pd.Grouper(key=date_col, freq="MS"))[sales_col]
        .sum()
    )

    # An incomplete last month would look like a fake drop, so leave it out
    last_data_date = df[date_col].max()
    dropped_partial = False
    if len(monthly_sales) > 0 and last_data_date.day < last_data_date.days_in_month:
        monthly_sales = monthly_sales.iloc[:-1]
        dropped_partial = True

    if len(monthly_sales) < 4:
        st.info(
            "At least 4 complete months of data are needed for a forecast. "
            f"Available: {len(monthly_sales)}."
        )
        return None

    horizon = st.slider("Months to forecast", 1, 6, 3)

    x_actual = np.arange(len(monthly_sales))
    slope, intercept = np.polyfit(x_actual, monthly_sales.values, 1)
    fitted = slope * x_actual + intercept
    spread = float(np.std(monthly_sales.values - fitted))

    x_future = np.arange(len(monthly_sales), len(monthly_sales) + horizon)
    forecast_values = np.clip(slope * x_future + intercept, 0, None)
    future_months = pd.date_range(
        monthly_sales.index[-1] + pd.offsets.MonthBegin(1),
        periods=horizon,
        freq="MS"
    )

    actual_part = pd.DataFrame({
        "Month": monthly_sales.index,
        "Sales": monthly_sales.values,
        "Type": "Actual"
    })
    # The forecast line starts at the last actual point so the chart connects
    forecast_part = pd.DataFrame({
        "Month": [monthly_sales.index[-1]] + list(future_months),
        "Sales": [monthly_sales.values[-1]] + list(forecast_values),
        "Type": "Forecast"
    })

    st.plotly_chart(
        px.line(
            pd.concat([actual_part, forecast_part]),
            x="Month", y="Sales", color="Type", markers=True,
            title=f"Monthly Sales: Actual and {horizon}-Month Forecast"
        )
    )

    forecast_table = pd.DataFrame({
        "Month": future_months.strftime("%b %Y"),
        "Forecast Sales": forecast_values.round(0),
        "Likely Low": np.clip(forecast_values - spread, 0, None).round(0),
        "Likely High": (forecast_values + spread).round(0),
    })
    st.dataframe(forecast_table)

    average_month = float(monthly_sales.mean())
    if average_month > 0:
        change_per_month = slope / average_month * 100
        if abs(change_per_month) < 0.5:
            st.info("➡️ Monthly sales are fairly flat.")
        elif change_per_month > 0:
            st.success(
                f"📈 Sales are trending up by about {change_per_month:.1f}% per month."
            )
        else:
            st.warning(
                f"📉 Sales are trending down by about {abs(change_per_month):.1f}% per month."
            )

    notes = (
        f"Based on {len(monthly_sales)} complete months. "
        "This is a simple straight-line trend: it does not know about "
        "seasons, festivals or promotions, so use it as a guide, not a promise."
    )
    if dropped_partial:
        notes += (
            f" The last month ({last_data_date.strftime('%b %Y')}) is "
            "incomplete, so it was left out."
        )
    if len(monthly_sales) < 6:
        notes += " Only a few months of history: treat this forecast as rough."
    st.caption(notes)

    return {
        "forecast_values": forecast_values,
        "future_months": future_months,
        "forecast_table": forecast_table,
    }


def show_whatif(sales_col, profit_col, total_sales, total_profit, profit_margin):
    """Price / demand / cost scenario simulator. Returns a dict or None."""
    st.markdown("---")
    st.markdown("## 🎛️ What-if Simulator")

    if not (sales_col and profit_col and total_sales and total_sales > 0):
        st.info("Sales and Profit columns are needed for the simulator.")
        return None

    st.caption(
        "Uses the data selected by the filters above. "
        "Change the sliders to see the effect on sales and profit."
    )

    s1, s2, s3 = st.columns(3)
    with s1:
        price_change = st.slider("Price change (%)", -30, 30, 0)
    with s2:
        elasticity = st.slider(
            "Demand elasticity", -3.0, 0.0, -1.0, 0.1,
            help="How strongly customers react to price. "
                 "-1.0 means a 10% price rise cuts units sold by about 9%."
        )
    with s3:
        cost_change = st.slider("Cost per unit change (%)", -30, 30, 0)

    price_ratio = 1 + price_change / 100
    volume_ratio = price_ratio ** elasticity
    current_cost = total_sales - total_profit

    new_sales = total_sales * price_ratio * volume_ratio
    new_cost = current_cost * volume_ratio * (1 + cost_change / 100)
    new_profit = new_sales - new_cost
    new_margin = new_profit / new_sales * 100 if new_sales > 0 else None

    margin_delta = None
    if new_margin is not None and profit_margin is not None:
        margin_delta = f"{new_margin - profit_margin:+.2f} pts"

    w1, w2, w3, w4 = st.columns(4)
    w1.metric("Sales", fmt(new_sales), delta=f"{new_sales - total_sales:+,.0f}")
    w2.metric("Profit", fmt(new_profit), delta=f"{new_profit - total_profit:+,.0f}")
    w3.metric(
        "Profit Margin",
        f"{new_margin:.2f}%" if new_margin is not None else "N/A",
        delta=margin_delta
    )
    w4.metric("Units Sold", f"{(volume_ratio - 1) * 100:+.1f}%")

    profit_gain = new_profit - total_profit
    if price_change == 0 and cost_change == 0:
        st.info("Move a slider to try a scenario.")
    elif profit_gain > 0:
        message = f"✅ This scenario increases profit by {profit_gain:,.0f}"
        if total_profit:
            message += f" ({profit_gain / abs(total_profit) * 100:+.1f}%)"
        st.success(message + ".")
    elif profit_gain < 0:
        st.warning(f"⚠️ This scenario reduces profit by {abs(profit_gain):,.0f}.")
    else:
        st.info("This scenario leaves profit unchanged.")

    compare = pd.DataFrame({
        "Scenario": ["Current", "Current", "What-if", "What-if"],
        "Measure": ["Sales", "Profit", "Sales", "Profit"],
        "Amount": [total_sales, total_profit, new_sales, new_profit],
    })
    st.plotly_chart(
        px.bar(
            compare, x="Measure", y="Amount", color="Scenario",
            barmode="group", title="Current vs What-if"
        )
    )

    st.caption(
        "How it works: cost = sales - profit. A price change moves demand using "
        "the elasticity (units = price ratio ^ elasticity), and cost scales with "
        "units sold. Elasticity is an assumption you choose, it is not learned "
        "from your data."
    )

    return {
        "new_sales": new_sales,
        "new_profit": new_profit,
        "volume_ratio": volume_ratio,
    }


def _iqr_flags(series):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)


def show_anomaly(df, numeric_columns, product_col):
    """IQR-based anomaly detection (needs 30+ rows, compared within each product)."""
    st.markdown("---")
    st.subheader("🔍 AI Anomaly Detection")

    if not numeric_columns:
        st.info("No numeric columns available for anomaly detection.")
        return

    anomaly_column = st.selectbox("Select a numeric column:", numeric_columns)
    values = df[anomaly_column].dropna()

    if len(values) < 30:
        st.info(
            "Anomaly detection needs at least 30 rows. "
            f"Current rows: {len(values)}."
        )
        return

    is_anomaly = pd.Series(False, index=df.index)

    if product_col:
        # Compare each sale only with the same product (a laptop sale
        # should not look unusual just because accessories are cheaper).
        for _, group in df.groupby(product_col):
            if group[anomaly_column].notna().sum() >= 10:
                is_anomaly.loc[group.index] = _iqr_flags(group[anomaly_column])
        st.caption(f"Each row is compared with other rows of the same {product_col}.")
    else:
        is_anomaly = _iqr_flags(df[anomaly_column])
        st.caption("Rows are compared with the whole column (IQR rule).")

    is_anomaly = is_anomaly.fillna(False)
    anomaly_count = int(is_anomaly.sum())

    st.metric("Anomalies Detected", anomaly_count)

    if anomaly_count > 0:
        st.warning(f"⚠️ {anomaly_count} unusual values detected in {anomaly_column}.")
        st.dataframe(df[is_anomaly])
        st.info(
            "💡 Review these records: they may be data-entry errors, "
            "exceptional deals or real changes in performance."
        )
    else:
        st.success("✅ No unusual values detected.")