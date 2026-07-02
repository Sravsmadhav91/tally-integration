# Tally (TallyPrime) Integration — General Guide

A provider-agnostic reference for reading from and writing to **TallyPrime** programmatically
via its **HTTP-XML Gateway**. Nothing here is specific to one company — for company-specific
chart-of-accounts and posting conventions see the companion file
`puneet-keshav-earan-conventions.md`.

> Verified working against TallyPrime on Windows, gateway on `localhost:9000`, June 2026.

---

## 1. How Tally exposes data

TallyPrime can run a lightweight **HTTP server** that accepts XML requests and returns XML.
This is the **only safe, supported** way to read and write data programmatically.

- Default endpoint: `http://localhost:9000`
- Enable it in Tally: **F1 (Help) → Settings → Connectivity → Client/Server configuration →**
  set *TallyPrime acts as* = **Both** (or *Server*), Port = **9000**.
- It serves both **Export** (read) and **Import** (write) in the same endpoint.

### ⚠️ Prerequisites for the gateway to actually do work (learned the hard way)
1. **TallyPrime must be running** with the gateway enabled.
2. **The target company must be OPEN/loaded** in Tally. Every data request sets
   `<SVCURRENTCOMPANY>…</SVCURRENTCOMPANY>`, which only resolves for a company that's currently open
   → otherwise `Could not set 'SVCurrentCompany' to '…'`. (Exceptions that work with no company
   loaded: `List of Companies`, and the bare port check.) Multiple companies can be open;
   `SVCURRENTCOMPANY` picks which. For unattended runs, set Tally to *load the company on startup*.
3. **A valid licence is required for WRITES.** If Tally loses its (network) licence, every import
   fails — and can leave the import engine jammed (see §6, gotcha #1). Reads may still work; writes
   won't. After restoring the licence, reload the company.

### ⚠️ Do NOT touch the binary data files
The company data lives in numbered folders like `…\TallyPrime\data\<companyId>\` as proprietary
binary files (`Manager.1800`, `TranMgr.1800`, `Company.1800`, …). **Never read or modify these
directly** — the format is undocumented and you will corrupt the company. Always go through the
XML gateway.

---

## 2. Quick connectivity checks (Windows)

```powershell
# Is Tally running?
Get-Process -Name tally* -ErrorAction SilentlyContinue

# Is the gateway port open?
Test-NetConnection -ComputerName 127.0.0.1 -Port 9000 -InformationLevel Quiet
```

POST an XML request (use `curl.exe`, not PowerShell's `curl` alias):

```bash
curl.exe -s -X POST -H "Content-Type: text/xml" --data-binary @request.xml http://localhost:9000
```

Always send the file with `--data-binary @file.xml` (preserves the XML exactly). Write request
files as **UTF-8 without BOM** and with plain `\n` — do not let PowerShell rewrite them (it adds
BOM/CRLF and can break the request).

### List loaded companies (a good first probe)
```xml
<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
  <TYPE>Collection</TYPE><ID>List of Companies</ID>
 </HEADER>
 <BODY><DESC>
   <STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES>
   <TDL><TDLMESSAGE>
     <COLLECTION NAME="List of Companies" ISMODIFY="No">
      <TYPE>Company</TYPE>
      <NATIVEMETHOD>Name</NATIVEMETHOD>
      <NATIVEMETHOD>StartingFrom</NATIVEMETHOD>
      <NATIVEMETHOD>BooksFrom</NATIVEMETHOD>
     </COLLECTION>
   </TDLMESSAGE></TDL>
 </DESC></BODY>
</ENVELOPE>
```
The response's `<COMPANY NAME="…">` tells you the exact company name string — you must pass this
verbatim as `<SVCURRENTCOMPANY>` in subsequent requests when more than one company exists.

---

## 3. Reading data (Export)

Two main shapes of read request:

### (a) Collection export — for masters and lists
Best for ledgers, groups, stock items, voucher types, and simple voucher lists. You define an
ad-hoc `<COLLECTION>` and ask for specific `<NATIVEMETHOD>` fields.

```xml
<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
  <TYPE>Collection</TYPE><ID>LedColl</ID>
 </HEADER>
 <BODY><DESC>
   <STATICVARIABLES>
    <SVCURRENTCOMPANY>YOUR COMPANY NAME</SVCURRENTCOMPANY>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL><TDLMESSAGE>
     <COLLECTION NAME="LedColl" ISMODIFY="No">
      <TYPE>Ledger</TYPE>
      <NATIVEMETHOD>Name</NATIVEMETHOD>
      <NATIVEMETHOD>Parent</NATIVEMETHOD>
      <NATIVEMETHOD>OpeningBalance</NATIVEMETHOD>
      <NATIVEMETHOD>ClosingBalance</NATIVEMETHOD>
     </COLLECTION>
   </TDLMESSAGE></TDL>
 </DESC></BODY>
</ENVELOPE>
```
Swap `<TYPE>` for `Group`, `StockItem`, `VoucherType`, `Voucher`, `CostCentre`, `Currency`, etc.

For a **Voucher** collection, add a date window via static variables:
```xml
<SVFROMDATE TYPE="Date">20240401</SVFROMDATE>
<SVTODATE   TYPE="Date">20250331</SVTODATE>
```
Dates are always `YYYYMMDD`.

> ⚠️ **Narration quirk:** a Voucher *Collection* export with `<NATIVEMETHOD>Narration</NATIVEMETHOD>`
> often returns the narration **blank even when it exists**. To read true narrations, use the
> Voucher Register data export (below) instead.
>
> ⚠️ **`ClosingBalance` quirk:** a Ledger *Collection* with `<NATIVEMETHOD>ClosingBalance</NATIVEMETHOD>`
> also often returns **blank**. To get balances, use a report (Trial Balance / Ledger), an `Object`
> export with `<FETCH>ClosingBalance</FETCH>`, or just **sum the voucher allocations yourself** from a
> Voucher Register export (most reliable for a date-bounded P&L figure).
>
> ⚠️ **Tag format differs by export type:** a *Collection* export tags values like
> `<LEDGERNAME TYPE="String">…` / `<AMOUNT TYPE="Amount">…`, but the *Voucher Register* (Data) export
> uses plain `<LEDGERNAME>…` / `<AMOUNT>…`. Write parsers that tolerate both, and read the AMOUNT
> from *inside* the relevant block (e.g. `<ACCOUNTINGALLOCATIONS.LIST>`), not the first AMOUNT after a
> ledger name (many tags can intervene).
>
> ⚠️ **Cancelled vouchers** are hidden by default. To see them: Day Book → **F12** → *Show Cancelled
> Vouchers = Yes* (or the *Cancelled Vouchers* exception report). They keep their number but zero all
> entries — no P&L/balance impact.

### (b) Report / data export — for full vouchers with real fields
Use `TYPE=Data` with a built-in report `ID` (e.g. **Voucher Register** = the Day Book) to get the
complete voucher XML including real narrations, bank allocations, inventory entries, etc.

```xml
<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST>
  <TYPE>Data</TYPE><ID>Voucher Register</ID>
 </HEADER>
 <BODY><DESC>
   <STATICVARIABLES>
    <SVCURRENTCOMPANY>YOUR COMPANY NAME</SVCURRENTCOMPANY>
    <SVFROMDATE TYPE="Date">20250401</SVFROMDATE>
    <SVTODATE   TYPE="Date">20250401</SVTODATE>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
 </DESC></BODY>
</ENVELOPE>
```
> ⚠️ The date narrowing on this report is **not always honoured** — sometimes it returns the whole
> financial year. Always check the dates in the returned set and filter again in your own code
> rather than trusting `SVFROMDATE/SVTODATE`.

---

## 4. Core data structures

| Entity | What it is | Key fields |
|---|---|---|
| **Group** | Node in the chart-of-accounts tree (Assets/Liabilities/Income/Expense) | Name, Parent, IsRevenue, IsDeemedPositive |
| **Ledger** | An account you post to; belongs to exactly one Group | Name, Parent (=group), Opening/ClosingBalance |
| **VoucherType** | Transaction class (Receipt, Payment, Sales, Purchase, Journal, Contra, …) | Name, Parent, NumberingMethod |
| **StockItem** | An inventory item (can represent shares, goods, anything tracked by qty) | Name, Parent (=stock group), BaseUnits |
| **Voucher** | A single transaction = header + ≥2 ledger entries (Dr=Cr) | Date, VoucherTypeName, ledger entries, (optional) inventory entries |

### The accounting sign convention (critical)
Each ledger line carries `<ISDEEMEDPOSITIVE>` and a signed `<AMOUNT>`:
- **Debit leg:** `ISDEEMEDPOSITIVE = Yes`, `AMOUNT` is **negative**.
- **Credit leg:** `ISDEEMEDPOSITIVE = No`,  `AMOUNT` is **positive**.
- Within a voucher the signed amounts must net to **zero** (debits = credits).

### Inventory ("invoice") vouchers
A Sales/Purchase voucher can be inventory-bearing (`OBJVIEW="Invoice Voucher View"`,
`ISINVOICE=Yes`). It then contains `<ALLINVENTORYENTRIES.LIST>` blocks (stock item, qty, rate,
amount) and each inventory entry has a nested `<ACCOUNTINGALLOCATIONS.LIST>` mapping the value to a
ledger (e.g. a sales/purchase ledger). The cash/party side is a normal voucher-level ledger entry.

---

## 5. Writing data (Import)

### Voucher import skeleton
```xml
<ENVELOPE>
 <HEADER>
  <TALLYREQUEST>Import Data</TALLYREQUEST>
 </HEADER>
 <BODY>
  <IMPORTDATA>
   <REQUESTDESC>
    <REPORTNAME>Vouchers</REPORTNAME>
    <STATICVARIABLES>
     <SVCURRENTCOMPANY>YOUR COMPANY NAME</SVCURRENTCOMPANY>
    </STATICVARIABLES>
   </REQUESTDESC>
   <REQUESTDATA>

    <!-- ONE TALLYMESSAGE PER VOUCHER (see gotcha below) -->
    <TALLYMESSAGE xmlns:UDF="TallyUDF">
     <VOUCHER VCHTYPE="Receipt" ACTION="Create" OBJVIEW="Accounting Voucher View">
      <DATE>20260227</DATE>
      <EFFECTIVEDATE>20260227</EFFECTIVEDATE>
      <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
      <NARRATION>free-text description</NARRATION>
      <ALLLEDGERENTRIES.LIST>
       <LEDGERNAME>Some Income Ledger</LEDGERNAME>
       <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
       <AMOUNT>1000.00</AMOUNT>
      </ALLLEDGERENTRIES.LIST>
      <ALLLEDGERENTRIES.LIST>
       <LEDGERNAME>Some Bank Ledger</LEDGERNAME>
       <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
       <AMOUNT>-1000.00</AMOUNT>
      </ALLLEDGERENTRIES.LIST>
     </VOUCHER>
    </TALLYMESSAGE>

   </REQUESTDATA>
  </IMPORTDATA>
 </BODY>
</ENVELOPE>
```

- `ACTION="Create"` adds a new voucher. `"Alter"`/`"Delete"` work **only** if the voucher was
  created with an explicit `REMOTEID` attribute (see gotcha #10) — so set one on every voucher.
- Omit `<VOUCHERNUMBER>` to let Tally auto-number (matches "Auto Retain" numbering).
- The same envelope can also import **masters** (ledgers, stock items) — use the matching tags,
  e.g. `<LEDGER NAME="…" ACTION="Create"><PARENT>…</PARENT>…</LEDGER>`.

### Import response
```xml
<RESPONSE>
 <CREATED>1</CREATED> <ALTERED>0</ALTERED> <DELETED>0</DELETED>
 <LASTVCHID>7349</LASTVCHID> <ERRORS>0</ERRORS> <EXCEPTIONS>0</EXCEPTIONS>
</RESPONSE>
```
Check `CREATED` vs `EXCEPTIONS`/`ERRORS`. Any `<LINEERROR>…</LINEERROR>` describes a failure.
**Always read the created vouchers back** (Voucher Register export) and reconcile before trusting.

---

## 6. Import gotchas (learned the hard way)

1. **Import ONE voucher per HTTP request (the big one).** The `"Voucher date is missing … retry
   Split"` error is Tally's internal import-splitter failing on multi-voucher requests. One
   `<TALLYMESSAGE>` per voucher helps for *tiny* batches (≤5), but larger single requests still cut
   off (observed: a 43-voucher request created only the first 7, 36 exceptions). And even rapid-fire
   *single*-voucher requests start returning "retry Split" once Tally gets busy. The reliable
   pattern that works at scale (650+ vouchers):
   - **one voucher per request**, sent sequentially with a small delay (~50 ms) between them;
   - **retry on "retry Split"/exception** (it's transient — back off ~0.5 s and resend, up to ~6×);
   - this is safe because of **REMOTEID idempotency** (gotcha #9): a resend with the same REMOTEID
     just ALTERs the existing voucher — it does **not** duplicate. So you can re-run the whole
     import freely until every voucher reports created/altered with 0 exceptions.
   - **⚠️ Tally can get GLOBALLY STUCK after a sustained bulk run.** Observed: ~82 creates succeeded,
     then EVERY subsequent create (any voucher type, even isolated/slow) returned "retry Split /
     date missing" with CREATED 0 — i.e. the import engine jammed (often a modal popup left open in
     the Tally window, or a stuck import session). Fixes: in the Tally window press **Esc** to clear
     any dialog; if that doesn't restore it, **restart TallyPrime and reload the company**. Then
     RESUME slowly (pace ~1–2 s/voucher, re-run is idempotent). Prevention: don't hammer — modest
     pace, and consider pausing every N vouchers.
2. **Ledgers/stock items must exist first.** Importing a voucher that references a non-existent
   ledger fails (or silently creates a bad master, depending on settings). Create masters first,
   or include them in the same import ahead of the vouchers.
3. **Idempotency is your job.** Tally does not dedupe. Re-running an import creates duplicates.
   Before importing, **query what already exists** (by date + amount + ledger) and import only the
   gap. (See the gap-analysis pattern in the company conventions file.)
4. **File encoding.** Generate request XML as UTF-8 (no BOM), `\n` line endings. On Windows prefer
   generating with Python/Node over PowerShell here-strings.
5. **Dates** are `YYYYMMDD`. Provide both `<DATE>` and `<EFFECTIVEDATE>`.
6. **XML-escape `&` → `&amp;`** in any name (ledger/stock item/narration). A raw `&` (e.g. stock item `M&M25AUGFUT`) makes the whole request malformed → Tally replies `Unknown Request, cannot be processed`. Also escape `<`/`>`.
7. **Master (ledger/stock-item) import:** use `<REPORTNAME>All Masters</REPORTNAME>`, and include an **inner `<NAME>` tag** in addition to the `NAME="…"` attribute — omitting the inner `<NAME>` throws an EXCEPTION (CREATED 0). Minimal stock item create:
   ```xml
   <STOCKITEM NAME="ADANIGREEN25APRFUT" ACTION="Create">
     <NAME>ADANIGREEN25APRFUT</NAME>
     <PARENT>Share Stock Equity F O</PARENT>
     <BASEUNITS>nos</BASEUNITS>
     <COSTINGMETHOD>FIFO Perpetual</COSTINGMETHOD>
     <VALUATIONMETHOD>Avg. Price</VALUATIONMETHOD>
   </STOCKITEM>
   ```
8. **Inventory ("invoice") vouchers** must include a `<BATCHALLOCATIONS.LIST>` (GODOWN `Main Location`, BATCH `Primary Batch`, with qty+amount) inside each `<ALLINVENTORYENTRIES.LIST>`, plus a nested `<ACCOUNTINGALLOCATIONS.LIST>` (the P&L ledger) and a voucher-level `<LEDGERENTRIES.LIST>` (the party/cash ledger).
9. **RATE: supply `rate = amount ÷ qty` AND the exact `<AMOUNT>`.** If you send only AMOUNT+QTY, Tally keeps the exact amount but leaves the **rate blank** (it does NOT back-calculate on import). If you send a rounded RATE *and* the exact AMOUNT, Tally **stores the rate for display and honours your exact amount** (it does NOT recompute amount = rate×qty). So compute rate = amount/qty at full precision → populated, correct rate with zero amount drift.
10. **Stamp an explicit `REMOTEID` on every voucher** (e.g. `PKE-FO-20250401-RECLTD25APRFUT-B`). Two payoffs: (a) **delete/alter only work via an externally-set REMOTEID** — vouchers imported without one get a Tally-internal id that is NOT addressable (delete fails with "Voucher does not exist!" / "Cannot delete unnamed object" for REMOTEID/GUID/VCHKEY/MASTERID alike; such vouchers can only be removed manually in the UI). (b) **idempotency** — resending the same REMOTEID with `ACTION="Create"` ALTERs in place (CREATED 0, ALTERED 1), never duplicates, so imports are safely re-runnable. Delete pattern: `<VOUCHER REMOTEID="…" VCHTYPE="Purchase" ACTION="Delete"><DATE>…</DATE><VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME></VOUCHER>` → DELETED 1.
11. **Master import** uses `<REPORTNAME>All Masters</REPORTNAME>`; voucher import uses `<REPORTNAME>Vouchers</REPORTNAME>`.

---

## 7. Safety checklist before any write

1. Confirm the correct `SVCURRENTCOMPANY`.
2. Have the user take an **in-app backup** (Gateway of Tally → F3/Alt-Y → Backup). A file copy of
   the data folder while Tally is open is a weak secondary net only.
3. Generate the import XML and **show it for review** first.
4. Import a **small test batch**, read it back, reconcile, then bulk-import.
5. Re-read and reconcile totals against the source after bulk import.

---

## 8. Handy request recipes

| Goal | TYPE / ID | Notes |
|---|---|---|
| List companies | Collection / `List of Companies` | no company needed |
| All ledgers | Collection / `Ledger` | + Parent, balances |
| All groups | Collection / `Group` | chart-of-accounts tree |
| All stock items | Collection / `StockItem` | + Parent, BaseUnits |
| Voucher types | Collection / `VoucherType` | |
| Vouchers in a period | Collection / `Voucher` | + SVFROMDATE/SVTODATE (narration unreliable) |
| Full day book | Data / `Voucher Register` | real narrations & sub-lists; re-filter dates in code |
| Trial Balance | Data / `Trial Balance` | balances by ledger/group |
| Ledger statement | Data / `Ledger Vouchers` | set `SVLEDGERNAME` |

---

## 9. Reference

- Endpoint: `http://localhost:9000` (POST, `Content-Type: text/xml`).
- Export format token: `<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>`.
- Tally TDL / XML interchange is the underlying mechanism; collections + native methods let you
  pull almost any field without writing TDL files.
