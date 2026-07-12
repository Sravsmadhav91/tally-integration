# Answer key — practice sandbox

Spoilers. Try the exercises in [`README.md`](./README.md) first.

## The data at a glance

- ~28 ledgers + 1 unit + 2 stock items. **FY24-25** = 54 correct vouchers (42 core + 12 GST/TDS/loan/trade).
  **FY25-26** = 9 flawed vouchers (practice). Voucher types used: Receipt, Payment, Contra, Journal, Sales, Purchase.
- FY25-26 opens from FY24-25's carry-forward: **Practice Bank opening = ₹2,94,200** (the enrichment settles
  through Practice Bank 2, so Practice Bank — the reconciliation account — is untouched).
- Truth for the FY25-26 bank = [`practice_bank_statement.csv`](./practice_bank_statement.csv).

## FY24-25 enrichment — check figures (period Apr-24 to Mar-25)

| Ledger | Balance | Ledger | Balance |
|---|---|---|---|
| Practice Bank | 2,94,200 Dr | Loan from Director | 2,10,000 Cr (2,00,000 + 10,000 int) |
| Practice Bank 2 | 1,37,000 Dr | Loan to Staff | 50,000 Dr |
| Sales | 12,000 Cr | Professional Fees | 40,000 Dr |
| Input/Output CGST/SGST | 0 (set off) | Interest on Loan | 10,000 Dr |
| GST Payable / TDS Payable | 0 (paid/deposited) | Purchases | 40,000 Dr (30,000 credit + 10,000 GST buy) |

**Stock (inventory):** *Widget A* — Purchase 100 in @₹100, Sale 100 out @₹120 → **closing stock 0**. The
GST purchase/sale are **stock-tracked invoice vouchers** (Invoice Voucher View); the money legs are
identical to a plain accounting entry (Purchases 10,000 / Sales 12,000 / GST / party), so no balances
change — they just also move quantity. Widget B has no movement (a spare item to practise with).

## Lesson 0 (warm-up) — how each posts

| Source | Line | Voucher | Legs |
|---|---|---|---|
| Excel | Office rent - July | Payment | Dr Office Rent 25,000 / Cr Practice Bank 25,000 |
| Excel | Consulting fee - ABC | Receipt | Dr Practice Bank 55,000 / Cr Consulting Income 55,000 |
| Excel | Transfer to Bank 2 | Contra | Dr Practice Bank 2 10,000 / Cr Practice Bank 10,000 |
| Excel | Electricity bill (unpaid) | Journal | Dr Electricity 3,000 / Cr Vendor XYZ 3,000 |
| PDF | NEFT-CLIENT PQR | Receipt | Dr Practice Bank 40,000 / Cr Consulting Income 40,000 |
| PDF | ELECTRICITY BOARD | Payment | Dr Electricity 3,000 / Cr Practice Bank 3,000 |
| PDF | BANK CHARGES | Payment | Dr Bank Charges 150 / Cr Practice Bank 150 |

## Lesson — TDS from 26AS (answer)

Post each on its **cut date** (`Dr TDS Receivable / Cr income`), one per line:

| Date | Deductor | Section | TDS | Entry |
|---|---|---|--:|---|
| 25-Apr-2024 | ACME Payroll | 192 | 5,000 | Dr TDS Receivable / Cr Salary Income |
| 25-May-2024 | ACME Payroll | 192 | 5,000 | Dr TDS Receivable / Cr Salary Income |
| 25-Jun-2024 | ACME Payroll | 192 | 5,000 | Dr TDS Receivable / Cr Salary Income |
| 12-Jul-2024 | BLUECHIP Ltd | 194 | 800 | Dr TDS Receivable / Cr Dividend Received |
| 20-Aug-2024 | GREENCO Ltd | 194 | 600 | Dr TDS Receivable / Cr Dividend Received |
| ~~20-Aug-2024~~ | ~~GREENCO Ltd (Inactive)~~ | ~~194~~ | ~~600~~ | **SKIP — superseded/duplicate row** |

**`TDS Receivable` total = ₹16,400** (3×5,000 + 800 + 600) = 26AS **Active** total. The GREENCO **Inactive**
row is NOT claimable — booking it would overstate the credit by ₹600. Salary is split **per month**,
dividends **per company**, each on its own date — never a single year-end lump.

## Lesson — capital gains (answer)

Reconcile AIS ↔ broker, fill the zero-cost lots, then split. The three AIS lots with `cost = 0` (DELTA,
EPSILON, ZETA) get their cost from the broker's buy value (40,000 / 30,000 / 25,000).

| Scrip | Held | Term | Sale | Cost used | Gain/Loss | Note |
|---|---|---|--:|--:|--:|---|
| ALPHA | ~5 mo | STCG 111A | 95,000 | 80,000 | **+15,000** | |
| BETA | ~5 mo | STCG 111A | 1,12,000 | 1,20,000 | **−8,000** | short-term loss |
| GAMMA | ~3.5 yr | LTCG 112A | 1,40,000 | 50,000 | **+90,000** | bought 2022 → no grandfathering |
| DELTA | ~10 yr | LTCG 112A | 1,50,000 | **90,000** | **+60,000** | pre-2018: deemed cost = max(40k, min(FMV 90k, sale 150k)) = 90k |
| EPSILON | ~9.5 yr | LTCG 112A | 1,00,000 | **1,00,000** | **0** | pre-2018: max(30k, min(FMV 110k, sale 100k)) = 100k → gain floored to 0 |
| ZETA | ~14 mo | LTCG 112A | 45,000 | 25,000 | **+20,000** | AIS cost was 0 → filled from broker |

- **STCG (111A) net = ₹7,000** (15,000 − 8,000).
- **LTCG (112A) net = ₹1,70,000** (90k + 60k + 0 + 20k); after the **₹1,25,000** Sec 112A exemption →
  **taxable LTCG ₹45,000**.

**Traps this teaches:** (1) filing straight off AIS taxes the *full sale value* of the three zero-cost lots
(you'd overpay on ~₹95,000 of phantom gain); (2) skipping grandfathering over-taxes DELTA (110k vs 60k) and
EPSILON (70k vs 0). Reproduce: `python ../scripts/capital_gains.py --file capital_gains/trades.csv`.

## FY24-25 reference — why it balances

Income: Consulting 12×50,000 = 6,00,000 + Bank Interest 2,000 = **6,02,000**.
Expenses: Rent 12×20,000 = 2,40,000 + Purchases 30,000 + Electricity 4×3,000 = 12,000 +
Bank charges 4×200 = 800 + Salaries 4×15,000 = 60,000 = **3,42,800**. Net profit = **2,59,200**.
Capital 1,00,000 + profit 2,59,200 − drawings 40,000 = **3,19,200** closing capital =
Practice Bank 2,94,200 + Practice Bank 2 25,000 = **3,19,200** assets. Balances. ✓

## FY25-26 — the five planted issues → catch & fix

| # | Issue | Where | How it surfaces | Fix |
|---|---|---|---|---|
| 1 | June activity missing | statement has 4 June lines; book has none | net-daily-movement gap-check flags 02-Jun & 30-Jun | post 4 vouchers with REMOTEIDs |
| 2 | Duplicate May rent | `SEED-PAY-RENT-MAY` **and** `-DUP` (identical) | two 25,000 rent debits on 02-May; statement shows one | delete `SEED-PAY-RENT-MAY-DUP` |
| 3 | Same-day consolidation | book `SEED-REC-MAY` = 65,000; statement = 45,000 + 20,000 | **same net** on 02-May → nothing missing | do **nothing** (posting the split would double-count 65,000) |
| 4 | Misclassification | `SEED-PAY-PERSONAL` → *Purchases* | bank matches (not a recon gap); P&L shows Purchases inflated | journal `Dr Drawings 15,000 / Cr Purchases 15,000` |
| 5 | Pending year-end | June rent unpaid; bank interest 1,200 unbooked | rent paid Apr & May but not Jun; interest is a statement credit | accrue `Dr Office Rent 25,000 / Cr Rent Payable 25,000`; book interest as income (step 5) |

## Reconciliation math (FY25-26 Practice Bank)

```
Opening (b/f FY24-25)               2,94,200
Statement closing (truth)          3,44,164
Book bank as seeded (wrong)        2,90,964
Gap                                   53,200
  + delete duplicate May rent      +  25,000  -> 3,15,964
  + post June: +50,000 -3,000 +1,200 -20,000 = +28,200  -> 3,44,164  ✓ ties
```

Issues #3 and #4 do **not** change the bank balance — that's the point. #3 is a "don't double-post" trap;
#4 is a classification error you only catch by reviewing the P&L, not the bank.

## Expected FY25-26 end state (after all fixes)

- **Practice Bank** = ₹3,44,164 (ties to statement).
- **Purchases** = 18,000 (the 15,000 moved to Drawings).  **Drawings** = 15,000.
- **Office Rent** = 75,000 (Apr paid, May paid, Jun accrued).  **Rent Payable** = 25,000.
- **Consulting Income** = 1,75,000 (60,000 + 65,000 + 50,000).  **Bank Interest** = 1,200.

## Regenerating the files

All artefacts come from one source of truth (with built-in self-checks):
```bash
python seed_practice_data.py --emit
```
Edit the `LEDGERS` / `REF_2425` / `BOOK_2526` / `STATEMENT_2526` lists and re-emit to change the scenario.
