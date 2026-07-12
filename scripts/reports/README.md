# Custom reports

Every `.sql` file here becomes a report automatically — the **filename is the report name**. Run it with:

```bash
python ../tally_report.py --company "My Co" --from 20250401 --to 20260331 --report monthly-summary
```

## Add a new report in 30 seconds
1. Create `my-report.sql` here with a `SELECT` over the cached tables (below).
2. Run `--report my-report`. That's it — no code change.

Use `:arg` anywhere in the SQL to make it take a parameter (passed via `--arg "..."`), e.g. one ledger:
```sql
SELECT v.date, e.dr, e.cr FROM entries e JOIN vouchers v ON v.id = e.voucher_id
WHERE e.ledger = :arg ORDER BY v.date
```

## Cached tables you can query
| Table | Columns |
|---|---|
| `vouchers` | `id, date` (YYYYMMDD), `vtype, remoteid, narration` |
| `entries` | `voucher_id, ledger, dr, cr` (dr/cr positive; one row per ledger leg) |
| `inventory` | `voucher_id, stockitem, in_out` ('in'/'out'), `qty, amount` |
| `masters` | `name, parent` (ledger → group) |

## Ad-hoc, no file needed
```bash
python ../tally_report.py --company "My Co" --from 20250401 --to 20260331 \
  --sql "SELECT vtype, COUNT(*) FROM vouchers GROUP BY vtype ORDER BY 2 DESC"
```

The cache is built once per `company + from + to` (reused on later runs; `--refresh` to rebuild), so reports
are instant and never re-hit Tally's slow balance computation (quirks #5a).
