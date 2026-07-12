# Scripts

Reusable, config-driven Python helpers for the Tally gateway. **No client data** — set `COMPANY` and your
ledger map, then compose these into per-task scripts.

## `tally_io.py`
Core gateway I/O:
- `export(report_id, fromdate, todate)` — read any report as XML (Voucher Register, Trial Balance,
  Profit and Loss, List of Accounts).
- `build_voucher(remoteid, vtype, date, narration, legs)` / `post(xml)` — post a Payment/Receipt/Contra with
  an idempotent `REMOTEID` and retry.
- `journal(remoteid, date, legs, narration)` — post a Journal.
- `delete_voucher(remoteid, vtype, date)` — reverse a voucher by its REMOTEID.

`legs` = list of `(ledger, 'Dr'|'Cr', positive_amount)`; the builder asserts the voucher balances.

## `tally_report.py` — cached SQL reporting (read/analysis)
Pulls the Voucher Register for a date range **once** into a local SQLite cache, then runs any report
instantly as SQL — so analysis never re-hits Tally's slow (hang-prone) balance computation (quirks #5a).

```bash
python tally_report.py --list                                   # built-in reports
python tally_report.py --company "My Co" --from 20250401 --to 20260331 --report trial-balance
python tally_report.py ... --report ledger --arg "Bank A/c"     # parameterised (running balance)
python tally_report.py ... --sql "SELECT vtype,COUNT(*) FROM vouchers GROUP BY vtype"   # ad-hoc
python tally_report.py ... --report stock --out stock.xlsx      # save CSV/XLSX
python tally_report.py ... --report trial-balance --refresh     # force a fresh pull
```
- **Refresh for a timeframe:** just change `--from`/`--to` (a matching cache is reused; `--refresh` rebuilds).
- **Built-ins (SQL):** `trial-balance`, `group-summary`, `voucher-summary`, `daybook`, `tds`, `stock`, `ledger`.
- **Built-ins (computed):**
  - `pnl` — income vs expense by primary group (walks the group tree), signed, + net profit.
  - `bank-recon` — diff a bank ledger's book movement against a statement CSV **by net daily movement**
    (quirks #22); shows only mismatched dates + the total gap: `--report bank-recon --arg "Bank A/c" --statement stmt.csv`.
  - `tds-vs-26as` — book TDS-credit ledgers vs a 26AS CSV (Active only; Inactive/duplicate rows excluded):
    `--report tds-vs-26as --form26as 26as.csv`.
- **Add a report** = drop a `.sql` file in [`reports/`](./reports/) (filename = report name), or use `--sql`.
  Cached tables: `vouchers`, `entries(dr,cr)`, `inventory`, `masters` — see [`reports/README.md`](./reports/README.md).
- The cache (`.cache/*.sqlite`) holds client data and is **git-ignored** — never commit it.

## `import_sheet.py` — reviewed sheet → Tally (the write bulk-step)
Post vouchers from an Excel/CSV. **Dry-run by default** (validates each voucher balances and previews the
legs); add `--post` to write. Idempotent `REMOTEID`s.
```bash
python import_sheet.py --company "My Co" --file vouchers.csv           # dry-run
python import_sheet.py --company "My Co" --file vouchers.csv --post    # write
```
Schema (rows sharing a `remoteid` = one voucher): `remoteid, date, vtype, ledger, drcr, amount, narration`.
Template: [`voucher_sheet_template.csv`](./voucher_sheet_template.csv). Handles simple ledger vouchers
(Payment/Receipt/Contra/Journal); **item/GST invoices** need Invoice Voucher View — see the sample seed.

## `pdf_extract.py` — PDF → text/tables (the source-side helper)
Dump text or tables from a (optionally password-protected) PDF.
```bash
python pdf_extract.py --file AIS.pdf --password aaaaa1111a01011990     # unlock + text (PAN-lc + DOB)
python pdf_extract.py --file invoice.pdf --tables --out lines.csv      # tables (pdfplumber)
```
> **Prefer letting your AI assistant read the PDF directly** (better on odd layouts/scans). Use this only
> for **password-protected** docs (26AS/AIS/Form-16: PAN-lowercase + DOB `DDMMYYYY`) and bulk. **Prove the
> extraction is complete before importing** — recompute the **running balance** row-by-row if the source has
> one (else tie to total debits/credits, closing balance, txn count) (quirks #37).

**Round-trip:** `pdf_extract.py` (or AI reads the PDF) → structured **sheet** → `import_sheet.py --dry-run`
→ `--post` → `tally_report.py` to verify the balances moved. Read + write, one repo.

## The safe workflow (do this every time)
1. **Back up** in-app; confirm the **licence is active** (not Educational — quirks #2a).
2. **Gap-analyse**: `export('Voucher Register', fy_start, fy_end)`, parse what exists, diff against the source
   **by net daily movement** (owners consolidate — quirks #22), build the list of *missing* entries.
3. **Review**: write the proposed entries to an Excel sheet and have the accountant approve/correct it.
4. **Test small**: post 1–2 of each voucher type; read back; check `created`/`altered`, no exceptions.
5. **Bulk**: post one-per-request with a small throttle; each carries a stable `REMOTEID` (re-runnable).
6. **Reconcile**: re-export; confirm ledger balances tie to the statement/source to the rupee.

## REMOTEID scheme (suggestion)
`<TAG>-<subject>-<yyyymmdd>-<seq>` — stable across re-runs so re-sending ALTERs in place (never duplicates),
and lets you delete a batch cleanly if a review turns something up.

> Idempotent + reversible by design: same REMOTEID re-sent = alter, not duplicate; `delete_voucher` removes it.
> Always keep a human review gate before posting to live books.
