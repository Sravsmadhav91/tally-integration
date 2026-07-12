# Conventions — Company "«COMPANY NAME»"  (TEMPLATE — fill one per client)

> Copy this file, rename it (e.g. `<client>-conventions.md`), and fill every «placeholder» from the client's
> actual Tally + prior-year entries. This is what lets the AI post entries **indistinguishable from the owner's**.
> Keep it **private** (it contains client data) — do not commit it to a public/shared repo.

## 1. Identity & connection
- Company string (verbatim): «COMPANY NAME»
- Data folder (never touch): `…\TallyPrime\data\«companyId»\`
- Gateway: `http://localhost:9000` (confirm enabled; licence active, not Educational).

## 2. Chart of accounts — the ledgers you'll actually post to
List the real ledger names **verbatim** (misspellings and trailing spaces included) grouped by purpose, e.g.:
- Banks: «bank ledger names ↔ statement files»
- Broker / trading: «purchase / sale / party (broker) ledgers»
- Charges: «per-head charge ledgers»
- Income: «dividend / interest / salary ledgers and their P&L vs Capital grouping»
- Parties / loans: «landlords, lenders, related parties»
- Capital / drawings: «capital account, drawings, personal items that bypass P&L»

## 3. Voucher style conventions (MUST follow)
- Voucher types used per transaction kind (Payment / Receipt / Contra / Journal / Purchase / Sales).
- Sign convention (see quirks #17).
- **Narration style** — copy the owner's phrasing (e.g. `«PAID TO <payee>»`, `«RENT PAID FOR <MON> <yy>»`,
  `«PERSONAL EXP»`). Derive these by reading prior-year vouchers.
- Consolidation behaviour — does the owner book same-day items individually or consolidated? (quirks #22).

## 4. Posting recipes (mirror these exactly)
Document the exact Dr/Cr for each recurring transaction: trades, charges, dividends, bank receipts/payments/
contra, rent, salary, loan interest, etc. — with the source file each amount comes from.
- **TDS / tax credits:** how salary/dividend/interest TDS is booked — anchor to **Form 26AS** and date each
  deduction on its **cut date** (§192 salary per month; §194 dividend per company), not a year-end lump
  (quirks #36). Note whether income is booked **net-of-TDS then grossed up**, and any clearing account used
  (e.g. a salary clearing ledger under Loans & Advances).

## 5. Source files (the client's annual download set)
`«D:\<CLIENT>\<FY>\»` — broker exports + bank statements + Form-16/tax reports. Note each file's coverage
(quirks #30) and which bank ledger each statement maps to (quirks #35). Include **Form 26AS** (the TDS-credit
anchor — quirks #36) and **AIS/TIS** (cross-check gross income; remember AIS can carry duplicate/"Inactive"
rows, so reconcile TDS to 26AS). Tax PDFs are usually password-protected (commonly PAN-lowercase + DOB
`DDMMYYYY`).

## 6. The non-negotiable workflow: GAP ANALYSIS before any write
1. Read what's already in Tally for the FY (Voucher Register export; filter by type + ledger).
2. Build the source truth (statements / tradebook / tax-P&L).
3. **Diff by NET DAILY movement** (not just per-line — owners consolidate; quirks #22) → import only the missing.
4. One voucher per request, explicit `REMOTEID`, retry, **read back and reconcile to the statement/source**.
5. Produce a **review sheet for the accountant** before posting; tax-sensitive judgement stays with the CA.

## 7. FY «yy-yy» status (snapshot — update as work proceeds)
Track per category: dividends / trades / charges / bank / year-end journals / pending / CA flags / final P&L.
