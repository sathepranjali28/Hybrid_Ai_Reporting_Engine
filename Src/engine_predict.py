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
