# Quirks & Gotchas — consolidated quick reference

Every non-obvious trap discovered driving a TallyPrime company over the HTTP-XML gateway, in one place.
Mechanics detail lives in `tally-general-guide.md`; company-specific rules go in your own conventions file
(see `conventions-template.md`). Read this first to avoid re-discovering them.

---

## A. Gateway / connection
1. **Company must be OPEN in Tally** for any data request — `SVCURRENTCOMPANY` only resolves for a
   loaded company, else `Could not set 'SVCurrentCompany'`. (Exceptions: `List of Companies`, port check.)
2. **Writes need a valid licence.** If Tally loses its network licence, every import fails and the
   import engine can JAM (all subsequent creates fail with "retry Split") — fix the licence, reload
   the company.
2a. **EDUCATIONAL MODE date trap (licence inactive).** In Educational mode (no active licence), voucher
   import is allowed ONLY on the **1st, 2nd, and last day of each month**. Any other date is rejected with
   the *misleading* error `Voucher date is missing for: '<type>' voucher 1 … retry Split` — the date is
   present and correct; it's the licence. **Diagnostic:** if 1st/2nd/last-day dates import but mid-month
   dates fail, you're in Educational mode. Fix the licence (don't burn time editing XML).
3. **Never touch the binary files** in `…\data\<companyId>\`. Gateway only.

## B. Reading (Export)
4. **Collection `Narration` returns BLANK** even when it exists → use the **Voucher Register** data export.
5. **Getting ledger balances via the gateway is unreliable — and on a big book can HANG Tally.** A
   `Collection` with `ClosingBalance`/`ClosingQty`/`Stock Summary` often returns BLANK; and see #5a —
   fetching balances for a large multi-year book is very slow. To get a balance: read it in the **Tally
   UI** (the Ledger screen shows opening/closing instantly), reconstruct from the day book (#15), or use
   **Trial Balance** / **Profit and Loss** report exports (group-level; honour `SVFROMDATE`/`SVTODATE`).
5a. **★ The gateway is effectively SINGLE-THREADED — a heavy READ can freeze Tally (looks like a crash).**
   A whole-book `ClosingBalance` collection (balances for *all* ledgers), or a very large `Voucher
   Register` pull, forces Tally to recompute by replaying all history and can peg it for minutes; the UI
   stops responding. While it churns, **every new request queues behind it and times out**, so it
   cascades and looks dead. Safeguards: (a) **never fetch closing balances for ALL ledgers** on a big
   multi-year book — scope to one ledger/group (`CHILDOF`) or just read it in the UI; (b) set a
   **generous client timeout** (heavy exports need 3–5 min, not 60 s) so you don't fire retries that pile
   MORE work on the queue; (c) if it hangs, **stop hammering** — wait it out, or force-close & reopen
   Tally. **Reads never corrupt data** (only writes change the book) — a hung read is safe to kill; allow
   Tally's routine repair on reopen. **Imports (writes) are quick and do NOT cause this** — it's the
   balance-computation READS.
6. **Voucher Register date filter (`SVFROMDATE/SVTODATE`) is sometimes IGNORED** — may return the whole FY.
   Always re-filter in code by the dates returned. (The **Day Book** report often ignores the range too and
   returns only the current date — prefer Voucher Register for a full-FY pull.)
7. **Tag format differs by export type:** Collection uses `<LEDGERNAME TYPE="String">` / `<AMOUNT TYPE="Amount">`;
   Voucher Register uses plain `<LEDGERNAME>` / `<AMOUNT>`. Parse tolerant of both, and read the AMOUNT from
   *inside* the relevant block, not the first AMOUNT after a name.
8. **The real voucher element is `<VOUCHER …>`** — beware sub-tags like `<VOUCHERFBTCATEGORY>` /
   `<VOUCHERTYPENAME>` when slicing vouchers out of a big export (match `<VOUCHER[ >]`, not `<VOUCHER`).
9. **`<PARENT>` carries a `TYPE` attribute** in ledger exports (`<PARENT TYPE="String">…`) — match `<PARENT[^>]*>`.
10. **Cancelled vouchers hidden by default** — Day Book → F12 → *Show Cancelled Vouchers = Yes*.

## C. Writing (Import)
11. **One `<TALLYMESSAGE>` per voucher**, and at scale **one voucher per HTTP request** with throttle +
    retry — large multi-voucher requests fail with `"Voucher date is missing … retry Split"` (transient/retryable).
12. **Stamp an explicit `REMOTEID` on every voucher.** (a) delete/alter ONLY work via an externally-set
    REMOTEID; auto-assigned ones aren't addressable. (b) re-sending the same REMOTEID ALTERs in place
    (idempotent) — never duplicates, so imports are safely re-runnable, and you can change a voucher's date
    by re-sending with a new `<DATE>` under the same REMOTEID.
13. **XML-escape `&` → `&amp;`** in any name — a raw `&` makes the request malformed → `Unknown Request`.
14. **Master import** (`REPORTNAME=All Masters`): include an **inner `<NAME>` tag** (not just the `NAME="…"`
    attribute) or it throws. Costing fields work too (FIFO Perpetual / Avg. Price).
15. **Inventory ("item") invoice vouchers — import in INVOICE mode, or Tally silently rejects them.**
    A stock invoice needs ALL of: `VCHTYPE=Purchase`/`Sales` **with `OBJVIEW="Invoice Voucher View"` and
    `<ISINVOICE>Yes</ISINVOICE>`**; the **party + tax (GST) legs in voucher-level `<LEDGERENTRIES.LIST>`**
    (NOT `<ALLLEDGERENTRIES.LIST>`); each stock line in `<ALLINVENTORYENTRIES.LIST>` carrying a
    `<BATCHALLOCATIONS.LIST>` (GODOWN `Main Location`, BATCH `Primary Batch`) **and** a nested
    `<ACCOUNTINGALLOCATIONS.LIST>` → the purchase/sale ledger.
15a. **★ The failure mode is OPAQUE.** Put the party in `<ALLLEDGERENTRIES.LIST>` (the accounting-voucher
    shape) on a stock invoice and the import returns `<CREATED>0</CREATED><EXCEPTIONS>1</EXCEPTIONS>` with
    **no `<LINEERROR>`** — zero hint. The *same* silent `EXCEPTIONS=1` also means **F11 → Inventory is OFF**.
    So when a stock invoice throws it, check BOTH: (a) invoice-mode + `LEDGERENTRIES` shape, and (b) the
    Inventory feature (F11) — don't assume it's one. (An accounting-only Purchase/Sales — party in
    `ALLLEDGERENTRIES`, no inventory — imports fine; it's specifically the *stock* invoice that demands
    invoice mode.) General rule: `EXCEPTIONS>0` with `ERRORS=0` and no `LINEERROR` = a data-shape/feature
    problem Tally couldn't place, not a field-level validation error — re-check the voucher *structure*.
16. **RATE:** supply `rate = amount ÷ qty` AND the exact `<AMOUNT>` → Tally shows the rate and keeps the
    amount exact. Amount+qty alone leaves the rate BLANK (no back-calc on import).
17. **Sign convention:** `ISDEEMEDPOSITIVE=Yes` ⇒ Dr (negative `<AMOUNT>`); `No` ⇒ Cr (positive). Payment =
    party Dr / bank Cr; Receipt = income Cr / bank Dr; Contra for bank↔bank. Each voucher's legs sum to 0.
18. **Stock balances must be reconstructed from the day book:** net `ACTUALQTY` by inventory-entry
    `ISDEEMEDPOSITIVE` (Yes=in / No=out) across **ALL voucher types** — bonuses/splits are often booked via
    **Journal**, so counting only Purchase−Sales undercounts.
19. **Can't merge stock items via gateway rename** — `ACTION="Alter"` to an existing name fails
    ("already exists"). Workarounds: split the sell across both items, a stock journal transfer, or merge in the UI.
20. **0-value vouchers post fine** (worthless-expiry sales, bonus/split @₹0) — qty moves, amount 0.
21. **Formula-character trap when exporting review sheets:** an Excel cell starting with `= + - @` is read as
    a formula and corrupts the file — prefix a space or reword.

## D. Gap-analysis / data-quality patterns (watch for these in any book)
22. **★ Owners CONSOLIDATE same-day entries.** Multiple same-day small UPIs (or both landlords' rent) are
    often booked as ONE voucher. A gap-check matching individual statement lines by (date, amount) will NOT
    see them as covered and will RE-ENTER them → **double-counting**. **Gap-check by NET DAILY movement /
    account for consolidation, not line-by-line.** (This cost a 54-voucher double-count once; caught only by
    reconciling ledger balances to the statement.)
23. **Ledger names have quirks** — trailing spaces, misspellings. **Copy names verbatim**; "correcting" one
    creates a duplicate ledger.
24. **Stock-item names are inconsistent** — full names vs symbols, renames, embedded whitespace (`NAME\r\n`),
    placeholders, suffixes (`-X`, `-GB`, `#`). Map by ISIN/name; don't create duplicates (splits a holding).
25. **Placeholder "-CHECK" items** — owners sometimes park a reconciliation difference in a dummy item. Watch for these.
26. **Negative legacy holdings** (book over-sold in prior years) = prior-year data errors (missing buys /
    unrecorded corporate action). Fix as prior-year corrections, not current-year.
27. **Corporate actions not always recorded.** Book qty may be pre-split while the broker is post-split.
    **Diagnostic: book/tradebook qty ≠ broker holding qty ⇒ suspect a corporate action** (verify via broker
    bulletins / exchange circulars). Rights entitlement (RE) ≠ the share (different ISIN).
28. **Prior-year opening balances may not tie to the statement/broker** — reconcile the opening (last year's
    close) separately; a closing mismatch that equals the opening diff is a prior-year issue, not this year's.
29. **Inter-entity money** (e.g. an HUF or family member's account) can get routed through the wrong ledger —
    reclassify to a proper loan/capital ledger; keep separate legal entities out of the book.

## E. Source-file patterns (broker / bank statements)
30. **Each export's coverage differs** — check the "from … to …" header per file; a mid-year download stops
    at the download date. Re-export after year-end for a full-year set.
31. **Broker tax-P&L is the anchor for realized figures** — it has the realized breakdown (STCG/LTCG/intraday,
    F&O options/futures), a charges break-up, open positions, and a **tradewise-exits** sheet that includes
    expiry/settlement the raw tradebook omits. For F&O the raw tradebook ≠ filed P&L; anchor on the tax-P&L.
32. **Dividends file "Quantity" = holding at ex-date** (a powerful holdings cross-check). The "Net Dividend
    Amount" is often actually GROSS (qty×DPS); the bank credit is net of TDS.
33. **Holdings file "Quantity Available" EXCLUDES pledged** — sum Available + Pledged(Margin) + Pledged(Loan)
    + Discrepant for the true holding (shares pledged for F&O margin don't show as available).
34. **Broker funds-ledger won't tie to the book's broker-ledger by balance** — the broker ledger nets F&O at
    daily margin/obligation while the book may carry F&O at notional; the difference is **collateral/margin
    blocked** (span + exposure) on open positions, not a missing entry. Strip margin to reconcile the cash basis.
35. **Bank statements differ by bank** — identify each by the account number / holder header (statements from
    different banks reuse similar filenames). Interest is often credited on the 1st of the next period with a
    prior-day value date — decide value-date vs transaction-date for year-end.
36. **Form 26AS is the anchor for TDS credits** (like the tax-P&L is for trades). It lists every deduction by
    deductor, **section** (192 salary / 194 dividend / 194A interest), date, amount-paid and tax-deducted.
    Reconcile the book's TDS **to 26AS, dated on each deduction's CUT DATE** — salary TDS per month (§192),
    dividend TDS per company (§194), not one year-end lump. **AIS is supplementary and noisier:** it can carry
    **"Inactive"/duplicate** rows (a superseded correction) and figures that don't tie — use **26AS for the
    claimable amount**, AIS only to cross-check gross income. Common pattern: the book records income **net of
    TDS** (the bank credit), so **gross it up per the 26AS lines** (`Dr TDS <type>` / `Cr <income>`) to claim
    the credit; the check is *book-net + 26AS-TDS = 26AS-gross*, per payer. Mind the **ex-date vs receipt-date
    straddle** — a dividend paid just after/before year-end sits in a different year's 26AS than the
    receipt-basis income.
37. **PDF source → sheet → Tally: let the AI READ the PDF; don't trust a generic table parser.** Bank/
    invoice/tax PDFs vary wildly in layout, and one-size table extraction mangles them. Reliable flow: the AI
    reads the PDF directly (its Read tool does PDFs/images via vision) → produces a **review sheet** in the
    `import_sheet.py` schema (`remoteid,date,vtype,ledger,drcr,amount,narration`) → a human checks it →
    `import_sheet.py` (dry-run, then `--post`). Use `scripts/pdf_extract.py` only for what the AI can't read
    directly: **password-protected** PDFs (26AS/AIS/Form-16 — password is usually **PAN-lowercase + DOB
    `DDMMYYYY`**) and bulk. **Whatever the method, PROVE the extraction is complete before importing** — a
    missed/duplicated/mis-keyed line silently corrupts the book. **Strongest check: the running balance.** If
    the source prints one (bank statements do), recompute it from the opening balance + each extracted line and
    match the printed running balance **row by row** — that pinpoints the exact row where extraction slipped
    (a grand total alone can hide two offsetting errors). No running balance? Tie to whatever control figures
    the doc prints — **total debits, total credits, closing balance, and the transaction count**. Never
    auto-post straight from a PDF; keep the review gate.
38. **Capital gains: AIS shows the SALE but usually NOT your cost — fill it from the broker, then split.**
    The AIS/TIS equity-sale schedule lists every sale + consideration, but the **cost of acquisition is often
    ₹0** for old or off-market lots (the dept doesn't know your purchase price). Filing straight off AIS taxes
    the **full sale value** — a huge over-statement. Fill the missing cost from the **broker's capital-gains
    report** (it has the real buy value + dates), reconciling by ISIN, and check every AIS sale has a broker
    lot (and vice-versa) so nothing is unreported or double-counted. Then classify per lot: listed equity is
    **LTCG (§112A) if held > 12 months**, else **STCG (§111A)**. For LTCG on shares **bought before
    01-Feb-2018, apply grandfathering**: deemed cost = *higher of* (actual cost, *lower of* (FMV on 31-Jan-2018,
    sale consideration)) — the 2018 FMV can only shrink a gain, never create a loss. `scripts/capital_gains.py`
    does the split + grandfathering + a §112A-exemption summary from a normalised lot sheet; the AIS↔broker
    reconciliation is the human/AI step (see `sample/capital_gains/`). **Rates, the exemption (₹1.25L) and the
    holding-period rule are set by the Finance Act and change year to year — the tool classifies, the CA signs
    off.**
