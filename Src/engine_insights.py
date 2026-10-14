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
