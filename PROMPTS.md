# Things you can just *say* to the AI (copy-paste cheat-sheet)

You drive this by **talking in plain English** — no commands to memorise. Below are ready-made prompts;
swap the `<placeholders>` (`<Your Company>`, `<FY>` like `2025-26`, `<path>`, `<Bank>`) for your own.

> **Golden habit:** for anything that *writes* to a real book, add **"…show me before posting"** (or "dry-run
> it first"). The AI drafts, you approve. Reads and reports are always safe to run.
>
> **When data comes from a PDF**, add **"…and prove it's complete against the running balance"** (or the
> statement's total debits/credits + closing balance) — that catches a missed or duplicated line before it
> reaches the book.

## First, get set up / sanity-check
- "Is my Tally gateway working? List the companies you can see."
- "Use company `<Your Company>` for everything from now on."
- "What bank accounts and main ledgers does `<Your Company>` have?"
- "Read the prior year's entries and draft a conventions file for `<Your Company>` from `conventions-template.md`."

## Look at the books (reports — safe, read-only)
- "Show me a **trial balance** for `<FY>`."
- "Show me a **profit & loss** for `<FY>`."   *(uses the `pnl` report)*
- "Give me the **`<Bank>` ledger statement** for `<FY>` with a running balance."
- "Summarise vouchers by type for `<FY>`."   /   "Which ledgers moved the most this year?"
- "Export a **stock summary** to Excel for `<FY>`."

## Reconcile
- "**Reconcile `<Bank>`** for `<FY>` against the statement at `<path>` — show me only the mismatched dates."
- "Compare my **dividend and salary TDS** to my **26AS** at `<path>` — am I claiming the right amount?"
- "Does my P&L for `<FY>` tie to the broker tax-P&L at `<path>`? Explain any difference."

## Enter data (writes — always preview first)
- "**Enter the missing `<Bank>` transactions** for `<FY>` from the statement at `<path>`. Gap-analyse what's
  already in Tally, **show me a table before posting**, then post once I approve."
- "**Post the dividends** for `<FY>` from `<folder>` (net of TDS, on the bank-credit dates) — preview first."
- "**Read this invoice PDF** `<path>` and draft the purchase entry (with GST) — show me, don't post yet."
- "I have a reviewed sheet at `<path>` — **dry-run it**, then post it if it balances."
- "**Delete** the voucher with REMOTEID `<id>`."   *(reversible)*

## Year-end
- "Draft the **year-end journals** for `<FY>` (rent accrual, trade charges, interest, salary, TDS) from the
  source files — list them for my review before posting."
- "Split the salary/dividend **TDS by month/company** on the actual deduction dates from my 26AS."

## Tax cross-checks
- "Cross-check the book against my **AIS/TIS** at `<path>` (password `<pan-lowercase><ddmmyyyy>`) and flag differences."
- "Reconcile my **F&O** book P&L to the broker tax-P&L (account for MTM and open positions)."

## If something looks off
- "This balance doesn't match — trace where the difference comes from, with evidence (voucher dates/amounts)."
- "Tally seems stuck — what did the last command do, and is it safe?"  *(reads never corrupt data; see quirks #5a)*

---
New to the words here? See the [Glossary](./ENVIRONMENT.md#glossary-plain-english). New to setup? Start with
[`ENVIRONMENT.md`](./ENVIRONMENT.md) then the [`sample/`](./sample/) practice company.
