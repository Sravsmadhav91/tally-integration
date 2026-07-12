# Practice sandbox

Learn the toolkit against a **throwaway company** loaded with two years of data — never practise on a
real client's books.

- **FY2024-25** — a *complete, correct* reference year covering the everyday scenarios: multiple bank
  accounts, sales & purchases, **GST** (input/output + set-off), **TDS** (deduct + deposit), and
  **loans** (received/given + interest). Browse it as your template for what good entries look like.
- **FY2025-26** — a *half-done, deliberately-wrong* practice year that **opens from FY2024-25's
  carried-forward balances** (just like a real second year). It hides five planted issues for you to fix.

Answer key: [`ANSWERS.md`](./ANSWERS.md).

## Set up (5 minutes)

1. **TallyPrime → Create Company.** Any name. **Set "Financial year beginning from" = 1-Apr-2024** so it
   can hold both years. Keep **F11 → Inventory → "Maintain Inventory" = Yes** (needed for the two
   stock-tracked GST invoices). Load it; enable the gateway on port 9000 (see [`../SETUP.md`](../SETUP.md)).
2. **Load the data — pick one:**

   **A. Seed over the gateway** (also teaches how imports work):
   ```bash
   pip install -r ../requirements.txt
   python seed_practice_data.py --company "Your Company Name"
   ```
   **B. Import the XML natively in Tally:** Gateway → **Import** → **Masters** → [`practice_masters.xml`](./practice_masters.xml),
   then **Import** → **Vouchers** → [`practice_vouchers_2024-25.xml`](./practice_vouchers_2024-25.xml),
   then [`practice_vouchers_2025-26.xml`](./practice_vouchers_2025-26.xml).

   **C. Restore a ready-made company:** see [`binary-company/`](./binary-company/).

   You get **16 ledgers**, **42 correct FY24-25 vouchers**, **9 (flawed) FY25-26 vouchers**, and the
   FY25-26 bank statement [`practice_bank_statement.csv`](./practice_bank_statement.csv). All dates are the
   1st/2nd/last of a month, so it loads **even without a licence** (Educational mode).

---

## Lesson 0 — learn to enter data (do this first)

Before any reconciliation, get comfortable *posting* entries with your AI assistant. Two source files
(dated Jul–Sep 2025, outside the reconciliation window, so they don't disturb the sandbox):

**A. Voucher entry from an Excel** — open [`lesson0_transactions.xlsx`](./lesson0_transactions.xlsx). It
lists four transactions, one of each core type. Ask your assistant to post each as the named voucher
(the Dr/Cr columns tell you the two ledgers), then read the day book back to confirm:

| Date | Type | What you're learning |
|---|---|---|
| 02-07-2025 | **Payment** | money out of the bank (Dr expense, Cr bank) |
| 31-07-2025 | **Receipt** | money into the bank (Dr bank, Cr income) |
| 01-08-2025 | **Contra** | bank-to-bank transfer (no P&L effect) |
| 31-08-2025 | **Journal** | an adjustment with no bank line (bill received, unpaid) |

**B. Bank entry from a PDF** — open [`lesson0_bank_page.pdf`](./lesson0_bank_page.pdf), a 3-line mini
statement. Your assistant can read the PDF directly. Post each line: **money IN = Receipt, money OUT =
Payment**, matching the other ledger from the description.

> **Tip:** switch the period to FY24-25 (Alt+F2) and compare your Lesson 0 entries to the reference
> year's entries — they should look the same.
>
> **Optional cleanup:** the warm-up entries use `LESSON0-*` REMOTEIDs, so you can delete them when done
> (that also teaches the delete flow). They're outside Apr–Jun, so leaving them won't affect the exercises.

---

## Lesson — TDS from Form 26AS (book on the cut date)

This mirrors real filing work: **income arrives net of TDS, and you claim the credit from Form 26AS.**
Open [`mock_26as_FY2024-25.csv`](./mock_26as_FY2024-25.csv) — a mini 26AS with the proprietor's **salary
(§192)** and **dividend (§194)** deductions.

**The rule** (see [quirks #36](../quirks.md)): **book each TDS credit on the date it was CUT, per 26AS —
salary per month, dividend per company — never one year-end lump.** Each gross-up is
`Dr TDS Receivable / Cr <income head>` for the TDS amount.

Steps (post with `LESSON-TDS-*` REMOTEIDs; create `TDS Receivable`, `Salary Income`, `Dividend Received` as needed):
1. **Salary §192** — one entry per month on its date (25-Apr / 25-May / 25-Jun): `Dr TDS Receivable 5,000 / Cr Salary Income 5,000`.
2. **Dividend §194** — one entry per company on its date: BLUECHIP 12-Jul `800`, GREENCO 20-Aug `600`.
3. **Reconcile:** the `TDS Receivable` total must equal the 26AS **Active** TDS = **₹16,400**.
4. **The trap:** GREENCO appears **twice** — one row is **Inactive** (a superseded/duplicate filing). **Book it once (₹600), not twice.** 26AS "Inactive" rows — and AIS duplicates — are NOT claimable.

> Why per-date, per-payer? So the book's TDS ties to 26AS line-by-line, the full credit is claimed, and any
> mismatch is easy to trace. Lumping TDS at year-end hides shortfalls and breaks the 26AS reconciliation.
> (This is exactly the correction pattern used on a real book — see the toolkit's conventions template §4.)

---

## Lesson — PDF → sheet → bulk import

The real round-trip: turn a source **PDF** into a reviewed **sheet**, then post it in one shot with
`import_sheet.py`.

1. **Read the PDF.** Have your assistant read [`lesson0_bank_page.pdf`](./lesson0_bank_page.pdf) directly, or
   dump it: `python ../scripts/pdf_extract.py --file lesson0_bank_page.pdf`.
2. **Structure it** into the importer schema (`remoteid, date, vtype, ledger, drcr, amount, narration`) —
   money **IN = Receipt**, **OUT = Payment**, other ledger from the description. The finished sheet is
   [`lesson_pdf_sheet.csv`](./lesson_pdf_sheet.csv) (peek if stuck).
3. **Dry-run, then post:**
   ```bash
   python ../scripts/import_sheet.py --company "Your Co" --file lesson_pdf_sheet.csv          # preview + balance check
   python ../scripts/import_sheet.py --company "Your Co" --file lesson_pdf_sheet.csv --post   # write to Tally
   ```

> These are the **same three lines as Lesson 0's PDF** — post them *either* by hand (Lesson 0) *or* via the
> sheet (here), **not both** (they'd double up; `LPDF-*` vs `LESSON0-*` REMOTEIDs won't stop that — they're
> different vouchers). ⚠️ Before `--post`, **prove the extraction is complete** — recompute the statement's
> **running balance** from the opening + your lines and match it (or, with no running balance, tie to the
> total debits/credits and closing balance).

---

## Lesson — capital gains: AIS ↔ broker → STCG/LTCG split

At return time you reconcile the **same equity sales seen three ways** and produce a filing-ready split.
The files in [`capital_gains/`](./capital_gains/) are a synthetic six-scrip example:

- [`ais_extract.csv`](./capital_gains/ais_extract.csv) — the tax dept's view (every sale + consideration).
  Note three lots show **`cost_ais_reported = 0`**: AIS often **doesn't know your purchase price** for
  old / off-market lots.
- [`broker_report.csv`](./capital_gains/broker_report.csv) — the broker's view (real buy value + dates +
  its own Short/Long tag). This is what **fills the zero costs**.
- [`trades.csv`](./capital_gains/trades.csv) — the **reconciled, normalised** lot list (cost filled in),
  ready to classify.

**The task:**
1. **Reconcile & fill.** Match AIS to the broker by ISIN. Where AIS cost is 0, fill it from the broker's buy
   value (that's how `trades.csv` was built). Check every AIS sale consideration has a broker lot and
   vice-versa — a missing lot means an unreported (or double-counted) sale.
2. **Split into Sec 111A / 112A:**
   ```bash
   python ../scripts/capital_gains.py --file capital_gains/trades.csv --out gains.xlsx
   ```
   - **STCG (111A):** held ≤ 12 months → gain = sale − cost.
   - **LTCG (112A):** held > 12 months. For lots **bought before 01-Feb-2018**, **grandfathering** applies:
     deemed cost = *higher of* (actual cost, *lower of* (FMV on 31-Jan-2018, sale price)) — so the 2018 FMV
     can only shrink a gain, never create a loss.
3. **Expected result:** STCG net **₹7,000**; LTCG net **₹1,70,000** (2 lots grandfathered — DELTA capped to a
   ₹60,000 gain, EPSILON floored to ₹0); after the Sec 112A **₹1,25,000** exemption, taxable LTCG **₹45,000**.

> **Why this matters:** if you file straight off AIS, the zero-cost lots inflate your gain massively (you'd
> pay tax on the *full* sale value). And forgetting grandfathering over-taxes pre-2018 holdings. The tool
> classifies + totals; **your CA confirms the rates and thresholds** for the year (they change by Budget).
> See [quirks #38](../quirks.md).

---

## The reference year (FY2024-25)

Set the period to **FY24-25** and open the day book / trial balance. It's a clean, balanced year covering
what an accountant meets daily — use any entry as a copy-me template:

| Scenario | Voucher(s) to study |
|---|---|
| Capital, monthly rent & consulting, quarterly overheads, drawings, bank interest | `REF-CAP`, `REF-RENT-*`, `REF-INC-*`, `REF-ELEC/CHG/SAL-*`, `REF-DRW`, `REF-INT` |
| Bank-to-bank transfer | `REF-CON-01` (Contra) |
| Credit purchase → payment (creditor cycle) | `REF-PUR-01`, `REF-VPAY-01` |
| **GST purchase — stock invoice** (Widget A: 100 in @₹100 + CGST + SGST) | `REF-GSTPUR-01` |
| **GST sale — stock invoice + collection** (Widget A: 100 out @₹120; debtor cycle) | `REF-GSTSAL-01`, `REF-GSTSAL-REC` |
| **GST set-off & payment** | `REF-GST-SETOFF`, `REF-GST-PAY` |
| **TDS** (deduct on a bill, pay net, deposit TDS) | `REF-TDS-BILL`, `REF-TDS-PAYCON`, `REF-TDS-DEPOSIT` |
| **Loans** (received, interest accrued, given) | `REF-LOAN-IN`, `REF-LOAN-INT`, `REF-LOAN-GIVEN` |

GST/TDS are posted as **explicit ledger amounts** (Dr/Cr), not via Tally's tax-computation engine, so the
entries stay portable across versions. The GST/TDS/loan/trade entries settle through **Practice Bank 2**,
so **Practice Bank stays at ₹2,94,200** — which carries forward as the FY25-26 opening for the exercises.

> **Inventory / stock:** the GST purchase & sale above are **stock-tracked invoice vouchers** (item
> *Widget A*: 100 in @₹100, 100 out @₹120 → closing stock 0; same money as a plain accounting entry). They
> need **F11 Inventory = Yes** and import in **Invoice Voucher View**: party + GST in `LEDGERENTRIES.LIST`,
> goods in `ALLINVENTORYENTRIES.LIST` with a `BATCHALLOCATIONS` (godown *Main Location*) +
> `ACCOUNTINGALLOCATIONS`. ⚠️ **Common trap:** putting the party in `ALLLEDGERENTRIES.LIST` (voucher mode)
> throws `EXCEPTIONS=1` with no detail — stock invoices MUST use invoice mode. To watch **closing-stock
> valuation**, edit the sale qty to fewer than 100 and re-seed.

## The five planted issues (FY2025-26)

1. **A whole month missing** — June bank activity isn't in the book (it's in the statement).
2. **A duplicate** — May rent is entered twice; the statement shows it once.
3. **A same-day consolidation** — the statement has two 02-May receipts (ABC 45,000 + PQR 20,000); the
   book lumps them into one 65,000 line. Same net movement → nothing missing (the classic double-post trap).
4. **A misclassification** — the owner's personal shopping (15,000) is booked to *Purchases*, not *Drawings*.
5. **Pending year-end items** — June rent is unpaid (accrue it); bank interest (1,200) isn't booked.

## Exercises (do these with your AI assistant + the toolkit)

Work in the **FY25-26** period.

1. **Read it back.** Export the day book / voucher register; confirm the 9 FY25-26 vouchers.
2. **Trial balance & P&L.** Export both; note the numbers — you'll re-check after fixing.
3. **Reconcile the bank — the right way.** Compare `practice_bank_statement.csv` to Practice Bank's book
   entries **by net daily movement, not line-by-line** (quirks #22). Opening (b/f) = **₹2,94,200**;
   statement closing = **₹3,44,164**; book as seeded = **₹2,90,964** (gap ₹53,200). The gap-check should
   flag the June lines as *missing*, the duplicate May rent as *extra*, and the split 02-May receipts as
   *already covered* (do NOT re-post them). **Shortcut:** `python ../scripts/tally_report.py --company
   "Your Co" --from 20250401 --to 20260331 --report bank-recon --arg "Practice Bank" --statement
   practice_bank_statement.csv` prints exactly the mismatched dates and the ₹53,200 gap.
4. **Find & delete the duplicate.** Delete one of the two identical May-rent payments via its REMOTEID
   (`../examples/11-delete-voucher.xml`, `REMOTEID="SEED-PAY-RENT-MAY-DUP"`). Re-read to confirm.
5. **Post the missing June entries** (idempotent, with REMOTEIDs): Client ABC +50,000, Electricity −3,000,
   Salaries −20,000, Bank Interest +1,200. Re-reconcile — Practice Bank should now tie to **₹3,44,164**.
6. **Reclassify the misclassification.** `Dr Drawings 15,000 / Cr Purchases 15,000`. Re-check the P&L.
7. **Book a year-end accrual.** June rent unpaid → `Dr Office Rent 25,000 / Cr Rent Payable 25,000`.
8. **Idempotency.** Re-run the seed — everything reports **altered**, nothing duplicates.

## When you move to a real (larger) book

This sandbox is tiny, so every query is instant. On a **real multi-year book it is NOT** — remember
[quirks #5a](../quirks.md): the Tally gateway is effectively **single-threaded**, so a heavy read can
freeze it (looks like a crash) and cascade into timeouts. In particular:
- **Never fetch closing balances for *all* ledgers at once** — it forces Tally to replay all history and
  can peg it for minutes. Read a balance in the **Tally UI**, or scope the query to one ledger/group (`CHILDOF`).
- Give heavy exports a **generous client timeout** (minutes, not 60 s); don't fire retries that pile more work on.
- **Reads never corrupt data** (only writes change the book) — a hung read is safe to kill; imports don't cause this.

## Clean up

Delete the practice company in Tally when done (Gateway → Alt-F3 → Delete), or keep it and re-seed anytime.
