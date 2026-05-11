"""
PySpark version of the ETL transformation logic.

This file is included to show how the same local Pandas pipeline can be scaled
for larger enterprise datasets using Spark on EMR, Databricks, or another Spark platform.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, round as spark_round


spark = SparkSession.builder.appName("SupplyChainAnalyticsETL").getOrCreate()

orders = spark.read.option("header", True).option("inferSchema", True).csv("raw/orders.csv")
products = spark.read.option("header", True).option("inferSchema", True).csv("raw/products.csv")
inventory = spark.read.option("header", True).option("inferSchema", True).csv("raw/inventory_snapshots.csv")
contracts = spark.read.option("multiline", True).json("raw/supplier_contracts.json")

orders = orders.dropDuplicates()
orders = orders.fillna({"carrier": "Unknown"})

fact_orders = (
    orders
    .join(products, on="product_id", how="left")
    .join(contracts, on="supplier", how="left")
    .withColumn("revenue", col("quantity") * col("unit_price"))
    .withColumn("cost", col("quantity") * col("unit_cost"))
    .withColumn("profit", col("revenue") - col("cost"))
    .withColumn("profit_margin", spark_round(col("profit") / col("revenue"), 4))
    .withColumn("delivery_variance_days", col("actual_delivery_days") - col("planned_delivery_days"))
    .withColumn("delivery_status", when(col("delivery_variance_days") > 0, "Delayed").otherwise("On Time"))
    .withColumn(
        "contract_validation_flag",
        when((col("delivery_status") == "Delayed") & (col("risk_tier") == "High"), "Review Needed").otherwise("Pass")
    )
)

inventory = inventory.withColumn(
    "inventory_risk_flag",
    when(col("on_hand_units") < col("reorder_point"), "Below Reorder Point").otherwise("Healthy")
)

fact_orders.write.mode("overwrite").parquet("processed/fact_orders_parquet")
inventory.write.mode("overwrite").parquet("processed/inventory_parquet")

spark.stop()
