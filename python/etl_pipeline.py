"""
Enterprise Supply Chain KPI Analytics Pipeline
Author: Likith Chanda

Purpose:
Extract structured CSV and semi-structured JSON data, validate and cleanse it,
transform it into analytics-ready datasets, load it into a SQLite warehouse,
and generate KPI outputs for operational decision-making.
"""

import json
import os
import sqlite3
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
WAREHOUSE_DIR = os.path.join(BASE_DIR, "warehouse")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")


def ensure_directories():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(WAREHOUSE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_data():
    orders = pd.read_csv(os.path.join(RAW_DIR, "orders.csv"))
    products = pd.read_csv(os.path.join(RAW_DIR, "products.csv"))
    inventory = pd.read_csv(os.path.join(RAW_DIR, "inventory_snapshots.csv"))

    with open(os.path.join(RAW_DIR, "supplier_contracts.json"), "r") as file:
        contracts_json = json.load(file)

    contracts = pd.json_normalize(contracts_json)

    return orders, products, inventory, contracts


def create_data_quality_report(raw_orders, cleaned_orders):
    report = {
        "pipeline_run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_order_rows": len(raw_orders),
        "cleaned_order_rows": len(cleaned_orders),
        "duplicate_rows_removed": int(raw_orders.duplicated().sum()),
        "missing_values_before_cleaning": raw_orders.isna().sum().to_dict(),
        "missing_values_after_cleaning": cleaned_orders.isna().sum().to_dict(),
        "cancelled_orders": int((cleaned_orders["order_status"] == "Cancelled").sum()),
        "delayed_orders": int((cleaned_orders["delivery_status"] == "Delayed").sum())
    }

    with open(os.path.join(OUTPUT_DIR, "data_quality_report.json"), "w") as file:
        json.dump(report, file, indent=2)

    return report


def transform_data(orders, products, inventory, contracts):
    raw_orders = orders.copy()

    # Standardize column names
    orders.columns = orders.columns.str.strip().str.lower()
    products.columns = products.columns.str.strip().str.lower()
    inventory.columns = inventory.columns.str.strip().str.lower()
    contracts.columns = contracts.columns.str.strip().str.lower().str.replace(".", "_", regex=False)

    # Remove duplicate records
    orders = orders.drop_duplicates()

    # Convert dates
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    inventory["snapshot_date"] = pd.to_datetime(inventory["snapshot_date"], errors="coerce")

    # Handle missing values using business-safe defaults
    orders["carrier"] = orders["carrier"].fillna("Unknown")
    orders["quantity"] = orders["quantity"].fillna(orders["quantity"].median())
    orders["actual_delivery_days"] = orders["actual_delivery_days"].fillna(orders["planned_delivery_days"])

    # Fix data types
    orders["quantity"] = orders["quantity"].astype(int)
    orders["actual_delivery_days"] = orders["actual_delivery_days"].astype(int)

    # Join product and contract metadata
    fact_orders = orders.merge(products, on="product_id", how="left")
    fact_orders = fact_orders.merge(contracts, on="supplier", how="left")

    # Business calculations
    fact_orders["revenue"] = fact_orders["quantity"] * fact_orders["unit_price"]
    fact_orders["cost"] = fact_orders["quantity"] * fact_orders["unit_cost"]
    fact_orders["profit"] = fact_orders["revenue"] - fact_orders["cost"]
    fact_orders["profit_margin"] = fact_orders["profit"] / fact_orders["revenue"]
    fact_orders["delivery_variance_days"] = fact_orders["actual_delivery_days"] - fact_orders["planned_delivery_days"]
    fact_orders["delivery_status"] = fact_orders["delivery_variance_days"].apply(
        lambda x: "Delayed" if x > 0 else "On Time"
    )

    # SLA / contract validation
    fact_orders["contract_validation_flag"] = fact_orders.apply(
        lambda row: "Review Needed"
        if row["delivery_status"] == "Delayed" and row["risk_tier"] == "High"
        else "Pass",
        axis=1
    )

    # Inventory risk transformation
    inventory["inventory_risk_flag"] = inventory.apply(
        lambda row: "Below Reorder Point" if row["on_hand_units"] < row["reorder_point"] else "Healthy",
        axis=1
    )

    # Dimension tables
    dim_product = products.drop_duplicates("product_id")
    dim_supplier = contracts.drop_duplicates("supplier")
    dim_warehouse = fact_orders[["warehouse_id", "region"]].drop_duplicates()

    return raw_orders, fact_orders, inventory, dim_product, dim_supplier, dim_warehouse


def load_outputs(fact_orders, inventory, dim_product, dim_supplier, dim_warehouse):
    fact_orders.to_csv(os.path.join(PROCESSED_DIR, "fact_orders_clean.csv"), index=False)
    inventory.to_csv(os.path.join(PROCESSED_DIR, "inventory_clean.csv"), index=False)
    dim_product.to_csv(os.path.join(PROCESSED_DIR, "dim_product.csv"), index=False)
    dim_supplier.to_csv(os.path.join(PROCESSED_DIR, "dim_supplier.csv"), index=False)
    dim_warehouse.to_csv(os.path.join(PROCESSED_DIR, "dim_warehouse.csv"), index=False)

    db_path = os.path.join(WAREHOUSE_DIR, "supply_chain_analytics.db")
    conn = sqlite3.connect(db_path)

    fact_orders.to_sql("fact_orders", conn, if_exists="replace", index=False)
    inventory.to_sql("fact_inventory", conn, if_exists="replace", index=False)
    dim_product.to_sql("dim_product", conn, if_exists="replace", index=False)
    dim_supplier.to_sql("dim_supplier", conn, if_exists="replace", index=False)
    dim_warehouse.to_sql("dim_warehouse", conn, if_exists="replace", index=False)

    conn.close()


def generate_kpis_and_charts(fact_orders, inventory):
    kpi_summary = {
        "total_orders": int(fact_orders["order_id"].nunique()),
        "total_revenue": round(float(fact_orders["revenue"].sum()), 2),
        "total_profit": round(float(fact_orders["profit"].sum()), 2),
        "average_profit_margin": round(float(fact_orders["profit_margin"].mean()), 4),
        "on_time_delivery_rate": round(float((fact_orders["delivery_status"] == "On Time").mean()), 4),
        "contract_review_rate": round(float((fact_orders["contract_validation_flag"] == "Review Needed").mean()), 4),
        "inventory_risk_count": int((inventory["inventory_risk_flag"] == "Below Reorder Point").sum())
    }

    pd.DataFrame([kpi_summary]).to_csv(os.path.join(OUTPUT_DIR, "kpi_summary.csv"), index=False)

    region_perf = fact_orders.groupby("region", as_index=False).agg(
        total_revenue=("revenue", "sum"),
        total_profit=("profit", "sum"),
        avg_delivery_variance=("delivery_variance_days", "mean")
    )
    region_perf.to_csv(os.path.join(OUTPUT_DIR, "region_performance.csv"), index=False)

    program = fact_orders.groupby("category", as_index=False).agg(
        total_revenue=("revenue", "sum"),
        total_profit=("profit", "sum"),
        avg_margin=("profit_margin", "mean")
    )
    program.to_csv(os.path.join(OUTPUT_DIR, "category_profitability.csv"), index=False)

    # Chart 1
    plt.figure(figsize=(9, 5))
    region_perf.sort_values("total_profit").plot(kind="barh", x="region", y="total_profit", legend=False)
    plt.title("Total Profit by Region")
    plt.xlabel("Total Profit")
    plt.ylabel("Region")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "profit_by_region.png"))
    plt.close()

    # Chart 2
    status_counts = fact_orders["delivery_status"].value_counts()
    plt.figure(figsize=(7, 5))
    status_counts.plot(kind="bar")
    plt.title("Delivery Status Distribution")
    plt.xlabel("Delivery Status")
    plt.ylabel("Order Count")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "delivery_status_distribution.png"))
    plt.close()

    # Chart 3
    inventory_counts = inventory["inventory_risk_flag"].value_counts()
    plt.figure(figsize=(7, 5))
    inventory_counts.plot(kind="bar")
    plt.title("Inventory Risk Summary")
    plt.xlabel("Inventory Risk Flag")
    plt.ylabel("Snapshot Count")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "inventory_risk_summary.png"))
    plt.close()

    return kpi_summary


def main():
    ensure_directories()
    orders, products, inventory, contracts = extract_data()
    raw_orders, fact_orders, inventory, dim_product, dim_supplier, dim_warehouse = transform_data(
        orders, products, inventory, contracts
    )
    create_data_quality_report(raw_orders, fact_orders)
    load_outputs(fact_orders, inventory, dim_product, dim_supplier, dim_warehouse)
    generate_kpis_and_charts(fact_orders, inventory)
    print("ETL pipeline completed successfully.")


if __name__ == "__main__":
    main()
