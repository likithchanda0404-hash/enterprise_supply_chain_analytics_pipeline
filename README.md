# Enterprise Supply Chain KPI Analytics Pipeline

## Project Summary
This project demonstrates an end-to-end Data Analyst workflow for enterprise operations analytics. It uses structured CSV files and semi-structured JSON data to build an automated ETL pipeline, perform data validation, create KPI-ready datasets, load a SQLite analytical warehouse, and generate SQL/Python-based business insights.

## Business Problem
Operations, finance, and supply chain teams need reliable KPIs to monitor revenue, profit, delivery performance, supplier contract risk, and inventory risk. Raw operational data often contains duplicates, missing values, inconsistent formats, and contract validation gaps. This project solves that by creating a repeatable analytics pipeline.

## Tools Used
- Python
- Pandas
- SQL
- SQLite
- PySpark template
- Airflow DAG template
- Matplotlib
- Power BI-ready dataset
- CSV and JSON data sources

## Folder Structure
```text
raw/                Raw CSV and JSON data
python/             Pandas ETL pipeline
pyspark/            Scalable PySpark ETL version
sql/                Business analysis SQL queries
warehouse/          SQLite analytical warehouse
processed/          Clean transformed outputs
outputs/            KPI summaries, quality report, and charts
dashboard/          HTML KPI dashboard
powerbi/            Power BI-ready CSV, DAX, and build guide
airflow/            Airflow DAG scheduling template
docs/               Video script and explanation
```

## ETL Workflow
1. Extract orders, products, inventory, and supplier contract data from CSV and JSON.
2. Transform data by removing duplicates, handling missing values, standardizing fields, joining datasets, and creating business rules.
3. Validate data quality through row counts, missing value checks, and contract review flags.
4. Load clean data into a SQLite warehouse using fact and dimension-style tables.
5. Generate KPI outputs, SQL analysis, and dashboard-ready reporting data.

## Key KPIs
- Total Orders
- Total Revenue
- Total Profit
- Average Profit Margin
- On-Time Delivery Rate
- Contract Review Rate
- Inventory Risk Count

## Business Insights
- Regions with lower delivery performance can be targeted for operational improvement.
- High-risk suppliers with delayed deliveries require contract review.
- Inventory items below reorder point should be prioritized to avoid stockouts.
- Category-level profit analysis helps finance and operations teams prioritize high-margin products.

## How to Run
```bash
cd enterprise_supply_chain_analytics_pipeline
python python/etl_pipeline.py
```

## Best Interview Explanation
This project matches a Data Analyst role that requires SQL, Python, data pipelines, data validation, KPI frameworks, operational analytics, and dashboard reporting.
