"""Tests for the helper functions in Src/engine_helpers.py."""
import pandas as pd

from engine_helpers import (
    build_docx_report,
    build_pdf_report,
    find_col,
    fmt,
    group_table,
    health_check,
    partial_month_note,
    to_date,
    to_number,
)


def make_clean_data():
    return pd.DataFrame({
        "Date": pd.date_range("2026-01-01", periods=10).strftime("%Y-%m-%d"),
        "Product": list("ABCDEABCDE"),
        "Sales": [100, 200, 300, 400, 500, 150, 250, 350, 450, 550],
        "Profit": [10, 20, 30, 40, 50, 15, 25, 35, 45, 55],
    })


def test_find_col_returns_first_match():
    assert find_col(["Date", "Total Sales", "Profit"], ["sales", "revenue"]) == "Total Sales"


def test_find_col_returns_none_when_missing():
    assert find_col(["Date", "Item"], ["sales", "revenue"]) is None


def test_fmt():
    assert fmt(1234.5) == "1,234.50"
    assert fmt(None) == "N/A"
    assert fmt(float("nan")) == "N/A"


def test_to_number_reads_rupee_and_comma_text():
    result = to_number(pd.Series(["₹1,200", "$ 3,000", "abc", None, "45"]))
    assert result[0] == 1200
    assert result[1] == 3000
    assert pd.isna(result[2])
    assert pd.isna(result[3])
    assert result[4] == 45


def test_to_number_keeps_numbers():
    assert to_number(pd.Series([10, 20])).tolist() == [10, 20]


def test_to_date_day_first_switch():
    text = pd.Series(["05/03/2026"])
    assert to_date(text, dayfirst=True)[0] == pd.Timestamp("2026-03-05")
    assert to_date(text, dayfirst=False)[0] == pd.Timestamp("2026-05-03")


def test_to_date_bad_value_becomes_missing():
    assert pd.isna(to_date(pd.Series(["not a date"]))[0])


def test_health_check_clean_data_scores_100():
    score, issues = health_check(make_clean_data(), "Sales", "Profit", None, "Date")
    assert score == 100
    assert all(count == 0 for count in issues.values())


def test_health_check_finds_problems():
    data = make_clean_data().astype({"Sales": object, "Profit": object})
    data.loc[0, "Sales"] = -5            # negative sales
    data.loc[1, "Sales"] = "abc"         # not a number
    data.loc[2, "Date"] = "not a date"   # invalid date
    data.loc[3, "Profit"] = None         # missing value
    data = pd.concat([data, data.iloc[[4]]], ignore_index=True)  # duplicate row
    score, issues = health_check(data, "Sales", "Profit", None, "Date")
    assert issues["Negative sales / quantity values"] == 1
    assert issues["Non-numeric values in number columns"] == 1
    assert issues["Invalid dates"] == 1
    assert issues["Missing values"] == 1
    assert issues["Duplicate rows"] == 1
    assert score < 100


def test_negative_profit_is_not_an_error():
    data = make_clean_data()
    data.loc[0, "Profit"] = -50
    score, issues = health_check(data, "Sales", "Profit", None, "Date")
    assert issues["Negative sales / quantity values"] == 0
    assert score == 100


def test_health_check_day_first_dates():
    data = make_clean_data()
    data["Date"] = ["13/01/2026"] * 10
    data["Sales"] = range(10)
    _, issues = health_check(data, "Sales", None, None, "Date", dayfirst=True)
    assert issues["Invalid dates"] == 0


def test_partial_month_note():
    last = pd.Timestamp("2026-09-12")
    assert "incomplete" in partial_month_note("2026-09", last)
    assert partial_month_note("2026-08", last) == ""
    assert partial_month_note("2026-09", pd.Timestamp("2026-09-30")) == ""


def test_group_table_margin():
    data = pd.DataFrame({
        "Product": ["A", "A", "B"],
        "Sales": [100, 100, 200],
        "Profit": [20, 20, 10],
    })
    table = group_table(data, "Product", "Sales", "Profit")
    row_a = table[table["Product"] == "A"].iloc[0]
    row_b = table[table["Product"] == "B"].iloc[0]
    assert row_a["Sales"] == 200
    assert row_a["Margin %"] == 20.0
    assert row_b["Margin %"] == 5.0


def test_group_table_without_profit_has_no_margin():
    data = pd.DataFrame({"Product": ["A", "B"], "Sales": [1, 2]})
    assert "Margin %" not in group_table(data, "Product", "Sales", None).columns


def test_reports_are_real_files():
    lines = ["Total sales are 100.", "Profit margin is 10%."]
    assert build_docx_report(lines).getvalue().startswith(b"PK")
    assert build_pdf_report(lines).getvalue().startswith(b"%PDF")
