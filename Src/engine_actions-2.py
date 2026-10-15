"""Target vs Actual tracker and a WhatsApp-ready summary (English / Marathi / Hindi)."""
import pandas as pd
import streamlit as st


def show_target(df, date_col, sales_col):
    """Track the latest month against a target the user types in. Returns a dict or None."""
    st.markdown("---")
    st.markdown("## 🎯 Target vs Actual")

    if not (date_col and sales_col):
        st.info("A valid Date column and a Sales column are needed for target tracking.")
        return None

    dated = df.dropna(subset=[date_col])
    if dated.empty:
        st.info("No dated rows are available for target tracking.")
        return None

    last_date = dated[date_col].max()
    month_start = last_date.replace(day=1).normalize()
    days_in_month = last_date.days_in_month
    month_rows = dated[
        (dated[date_col] >= month_start)
        & (dated[date_col] < month_start + pd.offsets.MonthBegin(1))
    ]
    month_sales = float(month_rows[sales_col].sum())
    month_label = last_date.strftime("%b %Y")

    # Suggested target: average of the earlier months (or this month if it is the only one)
    earlier = dated[dated[date_col] < month_start]
    if not earlier.empty:
        earlier_monthly = earlier.groupby(pd.Grouper(key=date_col, freq="MS"))[sales_col].sum()
        suggested = float(earlier_monthly.mean())
    else:
        suggested = month_sales
    suggested = max(1000.0, round(suggested / 1000) * 1000)

    target = st.number_input(
        f"Sales target for {month_label}",
        min_value=1.0,
        value=float(suggested),
        step=1000.0,
        help="Type the sales you want to reach this month."
    )

    pct = month_sales / target * 100
    remaining = max(target - month_sales, 0.0)
    month_open = last_date.day < days_in_month
    days_left = days_in_month - last_date.day if month_open else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Sales so far", f"{month_sales:,.0f}")
    c2.metric("Target", f"{target:,.0f}")
    c3.metric("Achieved", f"{pct:.1f}%")
    st.progress(min(max(pct / 100, 0.0), 1.0))

    needed_per_day = None
    projected = None

    if month_open:
        run_rate = month_sales / last_date.day
        projected = run_rate * days_in_month
        st.caption(
            f"Data runs until {last_date.strftime('%d %b %Y')}. "
            f"{days_left} day(s) are left in {month_label}."
        )
        if remaining <= 0:
            st.success(f"✅ Target already reached with {days_left} day(s) to spare.")
        else:
            needed_per_day = remaining / days_left
            st.info(
                f"To reach the target you need about {needed_per_day:,.0f} sales per day "
                f"for the remaining {days_left} day(s). "
                f"Your current average is {run_rate:,.0f} per day."
            )
            if projected >= target:
                st.success(
                    f"📈 At the current pace the month ends near {projected:,.0f}: on track."
                )
            else:
                st.warning(
                    f"⚠️ At the current pace the month ends near {projected:,.0f}, "
                    f"about {target - projected:,.0f} short of the target."
                )
    else:
        if remaining <= 0:
            st.success(f"✅ {month_label} is complete and the target was reached.")
        else:
            st.warning(
                f"⚠️ {month_label} is complete and the target was missed by {remaining:,.0f}."
            )

    return {
        "month": month_label,
        "target": target,
        "sales": month_sales,
        "pct": pct,
        "remaining": remaining,
        "days_left": days_left,
        "needed_per_day": needed_per_day,
        "projected": projected,
    }


TEXT = {
    "English": {
        "header": "📊 Sales Summary",
        "sales": "Total sales: {v}",
        "profit": "Total profit: {v}",
        "margin": "Profit margin: {v}%",
        "top_product": "Top product: {n}",
        "weak_region": "Weakest region: {n}",
        "up": "Sales rose {p}% in {m} compared to {prev}{open}",
        "down": "Sales fell {p}% in {m} compared to {prev}{open}",
        "open": " (month still running)",
        "forecast": "Forecast for next month: {v}",
        "target": "Target for {m}: {pct}% of {t} reached",
        "need": "About {v} sales per day needed to reach the target",
        "done": "Target reached ✅",
        "missed": "Target missed by {v}",
        "health": "Data health score: {v}%",
        "footer": "(The forecast is a simple trend, not a promise.)",
    },
    "मराठी": {
        "header": "📊 विक्री सारांश",
        "sales": "एकूण विक्री: {v}",
        "profit": "एकूण नफा: {v}",
        "margin": "नफा मार्जिन: {v}%",
        "top_product": "सर्वाधिक विक्री करणारे उत्पादन: {n}",
        "weak_region": "सर्वात कमकुवत विभाग: {n}",
        "up": "{m} मध्ये विक्री {prev} च्या तुलनेत {p}% ने वाढली{open}",
        "down": "{m} मध्ये विक्री {prev} च्या तुलनेत {p}% ने घटली{open}",
        "open": " (महिना अजून चालू आहे)",
        "forecast": "पुढील महिन्याचा अंदाज: {v}",
        "target": "{m} चे लक्ष्य {t} पैकी {pct}% पूर्ण",
        "need": "लक्ष्य गाठण्यासाठी रोज सुमारे {v} विक्री हवी",
        "done": "लक्ष्य पूर्ण झाले ✅",
        "missed": "लक्ष्य {v} ने हुकले",
        "health": "डेटा आरोग्य स्कोअर: {v}%",
        "footer": "(अंदाज हा साधा ट्रेंड आहे, हमी नाही.)",
    },
    "हिन्दी": {
        "header": "📊 बिक्री सारांश",
        "sales": "कुल बिक्री: {v}",
        "profit": "कुल मुनाफ़ा: {v}",
        "margin": "मुनाफ़ा मार्जिन: {v}%",
        "top_product": "सबसे ज़्यादा बिकने वाला उत्पाद: {n}",
        "weak_region": "सबसे कमज़ोर क्षेत्र: {n}",
        "up": "{m} में बिक्री {prev} की तुलना में {p}% बढ़ी{open}",
        "down": "{m} में बिक्री {prev} की तुलना में {p}% घटी{open}",
        "open": " (महीना अभी चल रहा है)",
        "forecast": "अगले महीने का अनुमान: {v}",
        "target": "{m} का लक्ष्य {t} में से {pct}% पूरा",
        "need": "लक्ष्य पाने के लिए रोज़ लगभग {v} बिक्री चाहिए",
        "done": "लक्ष्य पूरा हुआ ✅",
        "missed": "लक्ष्य {v} से चूका",
        "health": "डेटा हेल्थ स्कोर: {v}%",
        "footer": "(अनुमान एक साधारण ट्रेंड है, गारंटी नहीं।)",
    },
}


def _top(table, label_col, value_col, largest=True):
    if table is None or len(table) < 2 or label_col not in table or value_col not in table:
        return None
    idx = table[value_col].idxmax() if largest else table[value_col].idxmin()
    return str(table.loc[idx, label_col])


def show_summary(df, date_col, sales_col, product_col, region_col, product_table,
                 region_table, total_sales, total_profit, profit_margin,
                 forecast_result, target_result, health_score):
    """Build a short summary that can be copied and sent on WhatsApp."""
    st.markdown("---")
    st.markdown("## 💬 WhatsApp Summary")

    if not sales_col or total_sales is None:
        st.info("A Sales column is needed for the summary.")
        return None

    language = st.selectbox("Summary language", list(TEXT.keys()))
    t = TEXT[language]

    lines = [t["header"], ""]
    lines.append(t["sales"].format(v=f"{total_sales:,.0f}"))
    if total_profit is not None:
        lines.append(t["profit"].format(v=f"{total_profit:,.0f}"))
    if profit_margin is not None:
        lines.append(t["margin"].format(v=f"{profit_margin:.1f}"))

    best = _top(product_table, product_col, sales_col, largest=True)
    if best:
        lines.append(t["top_product"].format(n=best))
    weak = _top(region_table, region_col, sales_col, largest=False)
    if weak:
        lines.append(t["weak_region"].format(n=weak))

    if date_col:
        monthly = (
            df.dropna(subset=[date_col])
            .assign(Month=lambda d: d[date_col].dt.strftime("%Y-%m"))
            .groupby("Month")[sales_col].sum()
        )
        if len(monthly) >= 2 and monthly.iloc[-2] != 0:
            change = (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100
            last_date = df[date_col].max()
            is_open = last_date.day < last_date.days_in_month
            key = "up" if change >= 0 else "down"
            lines.append(t[key].format(
                p=f"{abs(change):.1f}", m=monthly.index[-1], prev=monthly.index[-2],
                open=t["open"] if is_open else ""
            ))

    if forecast_result:
        lines.append(t["forecast"].format(v=f"{forecast_result['forecast_values'][0]:,.0f}"))

    if target_result:
        lines.append(t["target"].format(
            m=target_result["month"], pct=f"{target_result['pct']:.0f}",
            t=f"{target_result['target']:,.0f}"
        ))
        if target_result["needed_per_day"] is not None:
            lines.append(t["need"].format(v=f"{target_result['needed_per_day']:,.0f}"))
        elif target_result["remaining"] <= 0:
            lines.append(t["done"])
        else:
            lines.append(t["missed"].format(v=f"{target_result['remaining']:,.0f}"))

    lines.append(t["health"].format(v=f"{health_score:.0f}"))
    lines.append("")
    lines.append(t["footer"])

    message = "\n".join(lines)
    st.code(message, language=None)
    st.caption("Use the copy icon at the top right of the box, then paste it into WhatsApp.")
    return message
