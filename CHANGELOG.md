# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); this project uses date-based releases.

## [0.1.0] — 2026-07-12 — first public release

The initial public toolkit: talk to an AI assistant on your PC and have it do your **TallyPrime** work —
data entry, bank reconciliation, and reporting — reading your PDFs / Excel / bank statements and **showing
you every entry before anything is saved**.

### Highlights

- **Read + write over the gateway** — [`scripts/tally_io.py`](./scripts/tally_io.py): export any report,
  post idempotent vouchers (stable `REMOTEID` → re-send alters instead of duplicating), journals, and
  delete/reverse.
- **Cached SQL reporting** — [`scripts/tally_report.py`](./scripts/tally_report.py): pull a date range
  **once** into a local SQLite cache, then run reports instantly as SQL, so analysis never re-hits Tally's
  slow, hang-prone balance computation. Ready-made: trial-balance, group-summary, voucher-summary, daybook,
  stock, ledger (running balance), TDS. **Computed:** `pnl`, `bank-recon` (book vs statement CSV by net
  daily movement), `tds-vs-26as`. Add a report by dropping a `.sql` file in `scripts/reports/`.
- **PDF → sheet → Tally pipeline** — [`pdf_extract.py`](./scripts/pdf_extract.py) (text/tables, handles
  password-protected 26AS/AIS/Form-16) → a reviewed Excel/CSV → [`import_sheet.py`](./scripts/import_sheet.py)
  (dry-run by default, `--post` to write). Prove completeness against the running balance before importing.
- **Capital-gains split** — [`capital_gains.py`](./scripts/capital_gains.py): classify equity sales into
  STCG §111A / LTCG §112A with **31-Jan-2018 grandfathering** and a §112A-exemption summary; the sample
  teaches the AIS↔broker reconciliation that fills AIS's missing (zero) costs.
- **Two-year practice sandbox** — [`sample/`](./sample/): a *correct* FY24-25 reference year (multi-bank,
  sales/purchase, GST, TDS, loans, inventory invoices) and a *flawed* FY25-26 practice year with **5 planted
  issues** + a mismatching bank statement. Includes **Lesson 0** (post from Excel; bank lines from a PDF),
  a TDS-from-26AS lesson, an 8-step graded exercise set, and an [answer key](./sample/ANSWERS.md).
- **Beginner onboarding (zero coding assumed)** — [`ENVIRONMENT.md`](./ENVIRONMENT.md): install an AI
  assistant (Antigravity or Claude Code, plus the 🇮🇳 free-Gemini-via-Jio route), turn on **auto/agent
  mode**, install Python & Tally; what the AI reads natively; using it on a real book; a plain-English
  glossary. Copy-paste prompts in [`PROMPTS.md`](./PROMPTS.md).
- **The mechanics & the traps** — [`tally-general-guide.md`](./tally-general-guide.md) and
  [`quirks.md`](./quirks.md) (38 non-obvious gotchas), plus 13 copy-paste XML
  [`examples/`](./examples/) and a per-company [`conventions-template.md`](./conventions-template.md).

### Safety model

AI **drafts**, the accountant **decides**. Reads are always safe; every write goes through a
dry-run/preview → approve → post gate. Idempotent + reversible by `REMOTEID`. Tax-sensitive judgement stays
with the CA.

### Known limitations

- The gateway is **single-threaded** — whole-book live-balance collections can hang Tally; use the cached
  SQL layer (quirks #5a).
- **Item/GST invoices** must use Invoice Voucher View (quirks #15a); simple ledger vouchers work via
  `import_sheet.py` directly.
- Tested primarily on Windows + TallyPrime. PDF power-tools (`pymupdf`, `pdfplumber`) are optional deps.
