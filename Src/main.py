import pandas as pd

df = pd.read_csv("Data/sales.csv")
total_sales = df["Sales"].sum()
total_profit = df["Profit"].sum()
average_sales = df["Sales"].mean()

print("Total Sales:", df["Sales"].sum())
print("Total Profit:", df["Profit"].sum())
print("Average Sales:", df["Sales"].mean())

top_product = df.groupby("Product")["Sales"].sum().idxmax()
print("Top Product:", top_product)

region_sales = df.groupby("Region")["Sales"].sum()
print("Region-wise Sales:")
print(region_sales)

import matplotlib.pyplot as plt

plt.figure(figsize=(8, 5))
region_sales.plot(kind="bar")

plt.title("Region-wise Sales")
plt.xlabel("Region")
plt.ylabel("Sales")
plt.tight_layout()
plt.show()

print("\nAI Insight:")
print("West region has the highest sales.")
print("Laptop is the top-selling product.")
print("Total sales and profit indicate positive business performance.")

# Automated Report

report = f"""
HYBRID DATA ANALYTICS & AI REPORTING ENGINE
--------------------------------------------

Total Sales: {total_sales}
Total Profit: {total_profit}
Average Sales: {average_sales:.2f}
Top Product: {top_product}

AI Insights:
- West region has the highest sales.
- Laptop is the top-selling product.
- Total sales and profit indicate positive business performance.
"""

with open("reports/report.txt", "w") as file:
    file.write(report)

print("\nReport generated successfully!")

