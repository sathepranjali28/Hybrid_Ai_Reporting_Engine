# 📊 Hybrid Data Analytics & AI Reporting Engine

Live app: https://hybridaireportingengine-gwqbcij6kqeuu9pdhzgcdg.streamlit.app/

## Problem
Small businesses often keep sales data in messy Excel files and have no analyst.
They cannot tell whether the data is reliable, or why sales went up or down.

## Solution
Upload a CSV or Excel file and the app:
1. Checks data quality and gives a Data Health Score.
2. Shows sales and profit trends (daily, weekly, monthly).
3. Explains why sales changed between two months, ranked by product or region.
4. Flags unusual records (anomalies).
5. Generates a business report as DOCX or PDF.

## Features
- Data Health Check: missing values, duplicates, invalid dates, negative values
- Filters by region, product and date range
- Profit margin and top/weakest product and region insights
- "Why Did Sales Change?" month-to-month comparison
- Anomaly detection (IQR rule, compared within each product)
- Downloadable DOCX and PDF reports

## Screenshots


![Metrics](screenshots/metrics.png)




![Data Health Check](screenshots/health_check.png)




![Why Did Sales Change](screenshots/why_changed.png)



## Tech Stack
Python, Streamlit, Pandas, Plotly, python-docx, ReportLab

## Run locally
    pip install -r requirements.txt
    streamlit run Src/app.py

## Sample data
`Data/sales_data.csv` is a generated sample dataset (1,000 rows).
Run `python Src/make_data.py` to regenerate it.