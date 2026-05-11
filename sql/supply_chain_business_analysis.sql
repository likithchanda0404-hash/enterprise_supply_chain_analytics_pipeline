-- Enterprise Supply Chain KPI Analytics
-- Run these queries against warehouse/supply_chain_analytics.db

-- 1. Executive KPI Summary
SELECT
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(profit_margin), 4) AS avg_profit_margin,
    ROUND(AVG(CASE WHEN delivery_status = 'On Time' THEN 1.0 ELSE 0 END), 4) AS on_time_delivery_rate,
    ROUND(AVG(CASE WHEN contract_validation_flag = 'Review Needed' THEN 1.0 ELSE 0 END), 4) AS contract_review_rate
FROM fact_orders;

-- 2. Region Performance with Ranking using Window Function
WITH region_summary AS (
    SELECT
        region,
        COUNT(DISTINCT order_id) AS total_orders,
        ROUND(SUM(revenue), 2) AS total_revenue,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(AVG(delivery_variance_days), 2) AS avg_delivery_variance
    FROM fact_orders
    GROUP BY region
)
SELECT
    region,
    total_orders,
    total_revenue,
    total_profit,
    avg_delivery_variance,
    RANK() OVER (ORDER BY total_profit DESC) AS profit_rank
FROM region_summary;

-- 3. Contract Validation Issues by Supplier
SELECT
    supplier,
    risk_tier,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN contract_validation_flag = 'Review Needed' THEN 1 ELSE 0 END) AS review_needed_orders,
    ROUND(AVG(CASE WHEN delivery_status = 'On Time' THEN 1.0 ELSE 0 END), 4) AS on_time_rate
FROM fact_orders
GROUP BY supplier, risk_tier
ORDER BY review_needed_orders DESC;

-- 4. Category Profitability
SELECT
    category,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(profit_margin), 4) AS avg_margin
FROM fact_orders
GROUP BY category
ORDER BY total_profit DESC;

-- 5. Inventory Risk by Product
SELECT
    product_id,
    COUNT(*) AS snapshots,
    SUM(CASE WHEN inventory_risk_flag = 'Below Reorder Point' THEN 1 ELSE 0 END) AS risk_snapshots
FROM fact_inventory
GROUP BY product_id
HAVING risk_snapshots > 0
ORDER BY risk_snapshots DESC;

-- 6. Monthly Operational Trend
SELECT
    strftime('%Y-%m', order_date) AS order_month,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(CASE WHEN delivery_status = 'On Time' THEN 1.0 ELSE 0 END), 4) AS on_time_delivery_rate
FROM fact_orders
GROUP BY strftime('%Y-%m', order_date)
ORDER BY order_month;
