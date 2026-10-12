import csv
import os
import random
from datetime import date, timedelta

random.seed(7)

products = {"Laptop": (55000, 0.15), "Mobile": (30000, 0.17), "Tablet": (25000, 0.15)}
regions = ["North", "South", "East", "West"]
start = date(2026, 1, 1)
rows = []

for _ in range(1000):
    d = start + timedelta(days=random.randint(0, 272))
    region = random.choice(regions)
    product = random.choices(list(products), weights=[3, 4, 3])[0]
    price, margin = products[product]
    qty = random.randint(5, 14)
    sales = round(price * random.gauss(1.0, 0.10) / 500) * 500
    if region == "South" and product == "Tablet" and d >= date(2026, 9, 1):
        sales = round(sales * 0.4 / 500) * 500
    profit = round(sales * (margin + random.gauss(0, 0.015)) / 100) * 100
    rows.append([d.isoformat(), region, product, sales, profit, qty])

rows.sort(key=lambda r: r[0])
os.makedirs("Data", exist_ok=True)

with open("Data/sales_data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "Region", "Product", "Sales", "Profit", "Quantity"])
    writer.writerows(rows)

print("Done:", len(rows), "rows")