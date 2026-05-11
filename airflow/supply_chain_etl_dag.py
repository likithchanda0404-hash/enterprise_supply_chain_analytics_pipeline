"""
Example Airflow DAG for scheduling the analytics pipeline.
This is a deployment template. It shows how the pipeline could run daily in an enterprise environment.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "analytics",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="enterprise_supply_chain_analytics_pipeline",
    default_args=default_args,
    description="Daily ETL for supply chain KPI reporting",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    run_etl = BashOperator(
        task_id="run_python_etl",
        bash_command="python /opt/analytics/python/etl_pipeline.py"
    )

    validate_outputs = BashOperator(
        task_id="validate_outputs",
        bash_command="test -f /opt/analytics/outputs/kpi_summary.csv"
    )

    run_etl >> validate_outputs
