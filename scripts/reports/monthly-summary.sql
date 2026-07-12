-- monthly-summary: total debits & credits per month across the cached range.
-- (Drop a .sql file here and its filename becomes a report name: --report monthly-summary)
SELECT substr(v.date, 1, 6) AS month,
       ROUND(SUM(e.dr), 2)  AS total_dr,
       ROUND(SUM(e.cr), 2)  AS total_cr
FROM vouchers v
JOIN entries e ON e.voucher_id = v.id
GROUP BY month
ORDER BY month
