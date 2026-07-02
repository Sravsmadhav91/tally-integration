# Tally + AI Integration Toolkit

A portable, **company-agnostic** toolkit for reading and writing a local **TallyPrime** company over its
built-in **HTTP-XML gateway** — designed so an accountant (with an AI assistant like Claude Code) can do
bulk data entry and reconciliation **safely** on live books.

Everything here is generic. To use it for a specific client, create a **conventions file** from
[`conventions-template.md`](./conventions-template.md) (one per company) — that's what lets the AI post
entries indistinguishable from the owner's own.

## Contents

| File | What it covers |
|---|---|
| [`tally-general-guide.md`](./tally-general-guide.md) | Gateway mechanics: enabling it, connectivity checks, reading (Export collections / Voucher Register / Trial Balance / P&L), data structures, writing (voucher Import), and a safety checklist. **Read first.** |
| [`quirks.md`](./quirks.md) | Consolidated quick-reference of every non-obvious trap (gateway, reading, writing, source files). Saves you re-discovering them. |
| [`conventions-template.md`](./conventions-template.md) | **Blank template** to build a per-company playbook: chart of accounts, posting recipes, narration/sign conventions, source files, and the gap-analysis workflow. |
| [`examples/`](./examples/) | Copy-paste XML request templates (list companies, read ledgers, read day book, import a receipt/trade). |
| [`scripts/`](./scripts/) | Reusable Python helpers: gap-check, idempotent voucher import (REMOTEID), and read-back reconciliation. Config-driven — set your company + ledger map at the top. |

## 30-second orientation

- Endpoint: `http://localhost:9000` — POST XML, `Content-Type: text/xml`.
- Send requests with: `curl.exe -s -X POST -H "Content-Type: text/xml" --data-binary @file.xml http://localhost:9000`
- Company string must match the loaded company **verbatim**.
- **Never** read/modify the binary files under `…\TallyPrime\data\<companyId>\` — use the gateway only.

## The golden rules before writing anything

1. **Back up in-app** (Gateway of Tally → F3/Alt-Y → Backup).
2. **Ensure the licence is active** (not "Educational mode" — see quirks #2/#2a; Educational mode rejects any
   voucher not dated on the 1st/2nd/last day of a month).
3. **Gap-analyse first** — owners enter data manually & partially; query what already exists and import only
   the missing items. **Compare by net daily movement, not just per-line** (owners consolidate same-day
   entries — matching line-by-line double-counts). Tally does NOT dedupe.
4. **One `<TALLYMESSAGE>` per voucher** on import, with an explicit **`REMOTEID`** (idempotent + reversible).
5. **Show the XML, test small, read back, reconcile to the statement/source** — then bulk.
6. **Match the owner's conventions exactly** (build a conventions file first).

> **AI drafts, the accountant decides.** Every batch should go through a human-reviewed sheet before posting,
> and tax-sensitive judgement (audit, loss set-off, prior-year errors) stays with the CA.
