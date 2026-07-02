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
