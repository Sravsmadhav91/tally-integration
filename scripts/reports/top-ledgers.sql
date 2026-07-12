-- top-ledgers: the 15 ledgers with the largest net movement in the cached range.
SELECT ledger,
       ROUND(SUM(dr) - SUM(cr), 2) AS net
FROM entries
GROUP BY ledger
ORDER BY ABS(SUM(dr) - SUM(cr)) DESC
LIMIT 15
