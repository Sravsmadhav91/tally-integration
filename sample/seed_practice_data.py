"""
seed_practice_data.py -- build a THROWAWAY TallyPrime practice company with TWO years of data:

  * FY2024-25  -- a COMPLETE, CORRECT reference year. Use it as your template for what good
                  entries look like when you enter the next year. It now covers the common
                  real-world scenarios: multiple banks, sales & purchases, GST (input/output +
                  set-off), TDS (deduct + deposit), and loans (received/given + interest).
  * FY2025-26  -- a HALF-DONE, deliberately-flawed year with 5 planted issues (see ANSWERS.md).
                  It OPENS from FY2024-25's carried-forward balances, like a real second year.

Never run this against a real client's company. It only writes to the company you name below.

COMPANY SETUP (once, in Tally)
  * Create a company (any name). Set "Financial year beginning from" = 1-Apr-2024 (holds both years).
    For the (optional) inventory template, also enable F11 -> Inventory -> Maintain Inventory = Yes.
    Load it; enable the gateway on port 9000 (see ../SETUP.md).
  * Name it here: edit COMPANY below, or pass  --company "Your Name".

LOAD IT
  A) Gateway (default):        python seed_practice_data.py --company "Your Name"
  B) Emit importable XML/CSV:  python seed_practice_data.py --emit

All voucher dates are the 1st / 2nd / last day of a month, so this loads even WITHOUT an active
licence (Educational mode). Gateway load is idempotent (re-run = alter). All amounts are illustrative.

NOTE on the accounting style: GST/TDS are posted as EXPLICIT ledger amounts (Dr/Cr), not via Tally's
GST/TDS auto-computation engine -- this keeps the sample import-portable across versions. Sales/Purchase
are accounting-mode invoices (no stock quantity). Stock/inventory needs F11 Inventory ON -- see the
optional template note in README.md.
"""
import sys, os, csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
HERE = os.path.dirname(os.path.abspath(__file__))
COMPANY = os.environ.get("TALLY_COMPANY", "Tally AI Practice")  # or pass --company "..."

LAST = {"202404": "30", "202405": "31", "202406": "30", "202407": "31", "202408": "31",
        "202409": "30", "202410": "31", "202411": "30", "202412": "31", "202501": "31",
        "202502": "28", "202503": "31"}
MONTHS_2425 = list(LAST.keys())

# ---------------------------------------------------------------- master ledgers
LEDGERS = [
    ("Practice Bank",     "Bank Accounts"),
    ("Practice Bank 2",   "Bank Accounts"),
    ("Cash",              "Cash-in-Hand"),
    ("Client ABC",        "Sundry Debtors"),
    ("Client PQR",        "Sundry Debtors"),
    ("Vendor XYZ",        "Sundry Creditors"),
    ("Consultant",        "Sundry Creditors"),
    ("Consulting Income", "Direct Incomes"),
    ("Sales",             "Sales Accounts"),
    ("Purchases",         "Purchase Accounts"),
    ("Office Rent",       "Indirect Expenses"),
    ("Bank Charges",      "Indirect Expenses"),
    ("Electricity",       "Indirect Expenses"),
    ("Salaries",          "Indirect Expenses"),
    ("Professional Fees", "Indirect Expenses"),
    ("Interest on Loan",  "Indirect Expenses"),
    ("Bank Interest",     "Indirect Incomes"),
    ("Rent Payable",      "Current Liabilities"),
    ("GST Payable",       "Current Liabilities"),
    ("TDS Payable",       "Current Liabilities"),
    ("Input CGST",        "Duties & Taxes"),
    ("Input SGST",        "Duties & Taxes"),
    ("Output CGST",       "Duties & Taxes"),
    ("Output SGST",       "Duties & Taxes"),
    ("Loan from Director", "Loans (Liability)"),
    ("Loan to Staff",     "Loans & Advances (Asset)"),
    ("Owner's Capital",   "Capital Account"),
    ("Drawings",          "Capital Account"),
]
UNITS = [("Nos",)]
# Stock items are masters for the OPTIONAL inventory template (needs F11 Inventory ON).
STOCKITEMS = [("Widget A", "Nos"), ("Widget B", "Nos")]

# ============================================================ FY2024-25 (correct)
def _ref_2425():
    v = [("REF-CAP-01", "Receipt", "20240401", "Owner capital introduced",
          [("Owner's Capital", "Cr", 100000), ("Practice Bank", "Dr", 100000)])]
    for ym in MONTHS_2425:
        v.append((f"REF-RENT-{ym}", "Payment", ym + "02", f"Office rent - {ym[4:6]}/{ym[:4]}",
                  [("Office Rent", "Dr", 20000), ("Practice Bank", "Cr", 20000)]))
        v.append((f"REF-INC-{ym}", "Receipt", ym + LAST[ym], f"Consulting fee - {ym[4:6]}/{ym[:4]}",
                  [("Consulting Income", "Cr", 50000), ("Practice Bank", "Dr", 50000)]))
    for ym in ("202406", "202409", "202412", "202503"):
        d = ym + LAST[ym]
        v.append((f"REF-ELEC-{ym}", "Payment", d, f"Electricity - qtr to {ym[4:6]}/{ym[:4]}",
                  [("Electricity", "Dr", 3000), ("Practice Bank", "Cr", 3000)]))
        v.append((f"REF-CHG-{ym}", "Payment", d, f"Bank charges - qtr to {ym[4:6]}/{ym[:4]}",
                  [("Bank Charges", "Dr", 200), ("Practice Bank", "Cr", 200)]))
        v.append((f"REF-SAL-{ym}", "Payment", d, f"Salaries - qtr to {ym[4:6]}/{ym[:4]}",
                  [("Salaries", "Dr", 15000), ("Practice Bank", "Cr", 15000)]))
    v += [
        ("REF-PUR-01", "Journal", "20240701", "Goods purchased on credit - Vendor XYZ",
            [("Purchases", "Dr", 30000), ("Vendor XYZ", "Cr", 30000)]),
        ("REF-VPAY-01", "Payment", "20240731", "Paid Vendor XYZ",
            [("Vendor XYZ", "Dr", 30000), ("Practice Bank", "Cr", 30000)]),
        ("REF-CON-01", "Contra", "20240501", "Transfer to Practice Bank 2",
            [("Practice Bank 2", "Dr", 25000), ("Practice Bank", "Cr", 25000)]),
        ("REF-DRW-01", "Payment", "20241102", "Owner drawings",
            [("Drawings", "Dr", 40000), ("Practice Bank", "Cr", 40000)]),
        ("REF-INT-01", "Receipt", "20250331", "Bank interest FY24-25",
            [("Bank Interest", "Cr", 2000), ("Practice Bank", "Dr", 2000)]),
    ]
    return v

REF_2425 = _ref_2425()

# ---- Enrichment (FY24-25): GST, TDS, loans. Routed via Practice Bank 2 so the FY25-26
# reconciliation on Practice Bank is untouched.
# NOTE: the GST purchase & sale are STOCK-TRACKED invoice vouchers -> see INV_2425 below; here we
# only keep their cash settlements (pay the vendor / collect from the client).
ENRICH_2425 = [
    ("REF-GSTPUR-PAY", "Payment", "20240831", "Paid Vendor XYZ (GST bill)",
        [("Vendor XYZ", "Dr", 11800), ("Practice Bank 2", "Cr", 11800)]),
    ("REF-GSTSAL-REC", "Receipt", "20240930", "Received from Client ABC",
        [("Practice Bank 2", "Dr", 14160), ("Client ABC", "Cr", 14160)]),
    # GST set-off (output - input) and payment of net GST
    ("REF-GST-SETOFF", "Journal", "20250331", "GST set-off (output less input)",
        [("Output CGST", "Dr", 1080), ("Output SGST", "Dr", 1080),
         ("Input CGST", "Cr", 900), ("Input SGST", "Cr", 900), ("GST Payable", "Cr", 360)]),
    ("REF-GST-PAY", "Payment", "20250331", "GST paid to government",
        [("GST Payable", "Dr", 360), ("Practice Bank 2", "Cr", 360)]),
    # TDS: professional fee 40,000, TDS @10% = 4,000 withheld; pay consultant net; deposit TDS
    ("REF-TDS-BILL", "Journal", "20241001", "Professional fee bill (TDS @10%)",
        [("Professional Fees", "Dr", 40000), ("TDS Payable", "Cr", 4000), ("Consultant", "Cr", 36000)]),
    ("REF-TDS-PAYCON", "Payment", "20241031", "Paid consultant (net of TDS)",
        [("Consultant", "Dr", 36000), ("Practice Bank 2", "Cr", 36000)]),
    ("REF-TDS-DEPOSIT", "Payment", "20241031", "TDS deposited to government",
        [("TDS Payable", "Dr", 4000), ("Practice Bank 2", "Cr", 4000)]),
    # Loans: received from director, interest accrued; loan given to staff
    ("REF-LOAN-IN", "Receipt", "20241101", "Loan received from Director",
        [("Practice Bank 2", "Dr", 200000), ("Loan from Director", "Cr", 200000)]),
    ("REF-LOAN-INT", "Journal", "20250331", "Interest on Director loan (accrued)",
        [("Interest on Loan", "Dr", 10000), ("Loan from Director", "Cr", 10000)]),
    ("REF-LOAN-GIVEN", "Payment", "20241201", "Loan given to staff",
        [("Loan to Staff", "Dr", 50000), ("Practice Bank 2", "Cr", 50000)]),
]

# ---- Inventory invoices (FY24-25): the GST purchase & sale as STOCK-TRACKED invoices.
# Widget A: 100 in @100 (buy) and 100 out @120 (sell) -> closing stock 0; same money as the
# accounting version (Purchases 10,000 / Sales 12,000 / same GST & party). Requires F11 Inventory=Yes.
# Import shape: "Invoice Voucher View" (ISINVOICE) with party+GST in LEDGERENTRIES.LIST and the goods
# in ALLINVENTORYENTRIES.LIST (BATCHALLOCATIONS godown "Main Location" + ACCOUNTINGALLOCATIONS).
# (rid, vtype, date, party, party_dp, party_amt, gst[(led,dp,amt)], item, qty, rate, inv_amt, acc_ledger, inv_dp)
INV_2425 = [
    ("REF-GSTPUR-01", "Purchase", "20240801", "Vendor XYZ", "No", 11800,
        [("Input CGST", "Yes", -900), ("Input SGST", "Yes", -900)],
        "Widget A", 100, 100, -10000, "Purchases", "Yes"),
    ("REF-GSTSAL-01", "Sales", "20240901", "Client ABC", "Yes", -14160,
        [("Output CGST", "No", 1080), ("Output SGST", "No", 1080)],
        "Widget A", 100, 120, 12000, "Sales", "No"),
]

# ============================================================ FY2025-26 (flawed)
BOOK_2526 = [
    ("SEED-PAY-RENT-APR",   "Payment", "20250402", "Office rent - April",
        [("Office Rent", "Dr", 25000), ("Practice Bank", "Cr", 25000)]),
    ("SEED-REC-ABC-APR",    "Receipt", "20250430", "Consulting fee - Client ABC (April)",
        [("Consulting Income", "Cr", 60000), ("Practice Bank", "Dr", 60000)]),
    ("SEED-CON-01",         "Contra",  "20250430", "Transfer to Practice Bank 2",
        [("Practice Bank 2", "Dr", 20000), ("Practice Bank", "Cr", 20000)]),
    ("SEED-PAY-PUR-01",     "Payment", "20250501", "Purchase of goods - Vendor XYZ",
        [("Purchases", "Dr", 18000), ("Practice Bank", "Cr", 18000)]),
    # PLANT #3 -- consolidation (statement splits this into ABC 45,000 + PQR 20,000).
    ("SEED-REC-MAY",        "Receipt", "20250502", "Consulting fees received (ABC + PQR)",
        [("Consulting Income", "Cr", 65000), ("Practice Bank", "Dr", 65000)]),
    ("SEED-PAY-RENT-MAY",   "Payment", "20250502", "Office rent - May",
        [("Office Rent", "Dr", 25000), ("Practice Bank", "Cr", 25000)]),
    # PLANT #2 -- duplicate of the line above.
    ("SEED-PAY-RENT-MAY-DUP", "Payment", "20250502", "Office rent - May",
        [("Office Rent", "Dr", 25000), ("Practice Bank", "Cr", 25000)]),
    ("SEED-PAY-CHG-MAY",    "Payment", "20250531", "Bank charges - May",
        [("Bank Charges", "Dr", 236), ("Practice Bank", "Cr", 236)]),
    # PLANT #4 -- misclassification: personal shopping booked to Purchases (should be Drawings).
    ("SEED-PAY-PERSONAL",   "Payment", "20250531", "Card payment - shopping",
        [("Purchases", "Dr", 15000), ("Practice Bank", "Cr", 15000)]),
    # PLANT #1 -- June missing.  PLANT #5 -- June rent unpaid + bank interest unbooked.
]

STATEMENT_2526 = [
    ("20250402", "RENT APRIL",           25000,  0),
    ("20250430", "NEFT-CLIENT ABC",      0,      60000),
    ("20250430", "TRANSFER TO A/C XX2",  20000,  0),
    ("20250501", "VENDOR XYZ PURCHASE",  18000,  0),
    ("20250502", "NEFT-CLIENT ABC",      0,      45000),   # PLANT #3 (split 1)
    ("20250502", "NEFT-CLIENT PQR",      0,      20000),   # PLANT #3 (split 2)
    ("20250502", "RENT MAY",             25000,  0),       # once only (book has 2)
    ("20250531", "BANK CHARGES",         236,    0),
    ("20250531", "DEBIT CARD-SHOPPING",  15000,  0),
    ("20250602", "NEFT-CLIENT ABC",      0,      50000),   # PLANT #1
    ("20250602", "ELECTRICITY BOARD",    3000,   0),       # PLANT #1
    ("20250630", "SAVINGS INTEREST",     0,      1200),    # PLANT #5
    ("20250630", "SALARY PAYMENT",       20000,  0),       # PLANT #1
]

# --------------------------------------------------------------------- computations
def bank_movement(vouchers, ledger="Practice Bank"):
    tot = 0
    for v in vouchers:
        for name, drcr, amt in v[4]:
            if name == ledger:
                tot += amt if drcr == "Dr" else -amt
    return tot

OPENING_2526 = bank_movement(REF_2425 + ENRICH_2425)         # FY24-25 closing = FY25-26 opening
STMT_MOVE = sum(cr - dr for _, _, dr, cr in STATEMENT_2526)
STMT_CLOSE = OPENING_2526 + STMT_MOVE
BOOK_CLOSE = OPENING_2526 + bank_movement(BOOK_2526)
assert OPENING_2526 == 294200, OPENING_2526      # enrichment must NOT touch Practice Bank
assert STMT_CLOSE == 344164, STMT_CLOSE
assert BOOK_CLOSE == 290964, BOOK_CLOSE

# --------------------------------------------------------------------- XML helpers
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))

def ledger_msg(name, parent):
    return (f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><LEDGER NAME="{esc(name)}" ACTION="Create">'
            f'<NAME>{esc(name)}</NAME><PARENT>{esc(parent)}</PARENT></LEDGER></TALLYMESSAGE>')

def unit_msg(name):
    return (f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><UNIT NAME="{esc(name)}" ACTION="Create">'
            f'<NAME>{esc(name)}</NAME><ISSIMPLEUNIT>Yes</ISSIMPLEUNIT><DECIMALPLACES>0</DECIMALPLACES>'
            f'</UNIT></TALLYMESSAGE>')

def stockitem_msg(name, unit):
    return (f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><STOCKITEM NAME="{esc(name)}" ACTION="Create">'
            f'<NAME>{esc(name)}</NAME><BASEUNITS>{esc(unit)}</BASEUNITS></STOCKITEM></TALLYMESSAGE>')

def voucher_msg(rid, vtype, date, narr, legs):
    entries = ""
    for ledger, drcr, amt in legs:
        dp = "Yes" if drcr == "Dr" else "No"
        signed = -abs(amt) if drcr == "Dr" else abs(amt)
        entries += (f'<ALLLEDGERENTRIES.LIST><LEDGERNAME>{esc(ledger)}</LEDGERNAME>'
                    f'<ISDEEMEDPOSITIVE>{dp}</ISDEEMEDPOSITIVE>'
                    f'<AMOUNT>{signed}</AMOUNT></ALLLEDGERENTRIES.LIST>')
    return (f'<TALLYMESSAGE xmlns:UDF="TallyUDF">'
            f'<VOUCHER REMOTEID="{esc(rid)}" VCHTYPE="{esc(vtype)}" ACTION="Create">'
            f'<DATE>{date}</DATE><VOUCHERTYPENAME>{esc(vtype)}</VOUCHERTYPENAME>'
            f'<NARRATION>{esc(narr)}</NARRATION>{entries}</VOUCHER></TALLYMESSAGE>')

def inventory_msg(rid, vtype, date, party, party_dp, party_amt, gst, item, qty, rate, inv_amt, acc_ledger, inv_dp):
    """A stock-tracked GST invoice (Invoice Voucher View). Party + GST go in LEDGERENTRIES.LIST;
    the goods go in ALLINVENTORYENTRIES.LIST with a BATCHALLOCATIONS (godown) + ACCOUNTINGALLOCATIONS."""
    led = f'<LEDGERENTRIES.LIST><LEDGERNAME>{esc(party)}</LEDGERNAME><ISDEEMEDPOSITIVE>{party_dp}</ISDEEMEDPOSITIVE><AMOUNT>{party_amt}</AMOUNT></LEDGERENTRIES.LIST>'
    for g, dp, amt in gst:
        led += f'<LEDGERENTRIES.LIST><LEDGERNAME>{esc(g)}</LEDGERNAME><ISDEEMEDPOSITIVE>{dp}</ISDEEMEDPOSITIVE><AMOUNT>{amt}</AMOUNT></LEDGERENTRIES.LIST>'
    return (f'<TALLYMESSAGE xmlns:UDF="TallyUDF">'
            f'<VOUCHER REMOTEID="{esc(rid)}" VCHTYPE="{esc(vtype)}" ACTION="Create" OBJVIEW="Invoice Voucher View">'
            f'<DATE>{date}</DATE><VOUCHERTYPENAME>{esc(vtype)}</VOUCHERTYPENAME>'
            f'<PARTYLEDGERNAME>{esc(party)}</PARTYLEDGERNAME><ISINVOICE>Yes</ISINVOICE>'
            f'<NARRATION>Goods {"bought" if vtype == "Purchase" else "sold"} with GST (stock-tracked) - {esc(party)}</NARRATION>'
            f'<ALLINVENTORYENTRIES.LIST><STOCKITEMNAME>{esc(item)}</STOCKITEMNAME><ISDEEMEDPOSITIVE>{inv_dp}</ISDEEMEDPOSITIVE>'
            f'<RATE>{rate}/Nos</RATE><AMOUNT>{inv_amt}</AMOUNT><ACTUALQTY>{qty} Nos</ACTUALQTY><BILLEDQTY>{qty} Nos</BILLEDQTY>'
            f'<BATCHALLOCATIONS.LIST><GODOWNNAME>Main Location</GODOWNNAME><BATCHNAME>Primary Batch</BATCHNAME>'
            f'<ACTUALQTY>{qty} Nos</ACTUALQTY><BILLEDQTY>{qty} Nos</BILLEDQTY><AMOUNT>{inv_amt}</AMOUNT></BATCHALLOCATIONS.LIST>'
            f'<ACCOUNTINGALLOCATIONS.LIST><LEDGERNAME>{esc(acc_ledger)}</LEDGERNAME><ISDEEMEDPOSITIVE>{inv_dp}</ISDEEMEDPOSITIVE>'
            f'<AMOUNT>{inv_amt}</AMOUNT></ACCOUNTINGALLOCATIONS.LIST></ALLINVENTORYENTRIES.LIST>'
            f'{led}</VOUCHER></TALLYMESSAGE>')

def envelope(reportname, messages):
    return ('<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA>'
            f'<REQUESTDESC><REPORTNAME>{reportname}</REPORTNAME><STATICVARIABLES>'
            f'<SVCURRENTCOMPANY>{esc(COMPANY)}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC>'
            '<REQUESTDATA>' + "".join(messages) + '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>')

def master_messages():
    return ([unit_msg(u[0]) for u in UNITS] +
            [ledger_msg(n, p) for n, p in LEDGERS] +
            [stockitem_msg(n, u) for n, u in STOCKITEMS])

# ------------------------------------------------------------------------ actions
def emit_files():
    with open(os.path.join(HERE, "practice_masters.xml"), "w", encoding="utf-8") as f:
        f.write(envelope("All Masters", master_messages()))
    with open(os.path.join(HERE, "practice_vouchers_2024-25.xml"), "w", encoding="utf-8") as f:
        f.write(envelope("Vouchers", [voucher_msg(*v) for v in REF_2425 + ENRICH_2425]
                         + [inventory_msg(*v) for v in INV_2425]))
    with open(os.path.join(HERE, "practice_vouchers_2025-26.xml"), "w", encoding="utf-8") as f:
        f.write(envelope("Vouchers", [voucher_msg(*v) for v in BOOK_2526]))
    with open(os.path.join(HERE, "practice_bank_statement.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Description", "Debit", "Credit", "Balance"])
        bal = OPENING_2526
        w.writerow(["01-04-2025", "OPENING BALANCE (b/f FY24-25)", "", "", bal])
        for d, desc, dr, cr in STATEMENT_2526:
            bal += cr - dr
            w.writerow([f"{d[6:8]}-{d[4:6]}-{d[0:4]}", desc, dr or "", cr or "", bal])
    print("Wrote practice_masters.xml, practice_vouchers_2024-25.xml, "
          "practice_vouchers_2025-26.xml, practice_bank_statement.csv")
    _print_expectations()

def _print_expectations():
    print(f"  FY24-25 closing Practice Bank (= FY25-26 opening) : {OPENING_2526:>10,}")
    print(f"  FY25-26 statement closing (truth)                 : {STMT_CLOSE:>10,}")
    print(f"  FY25-26 book bank as seeded (wrong)               : {BOOK_CLOSE:>10,}")
    print(f"  Gap to resolve                                    : {STMT_CLOSE - BOOK_CLOSE:>10,}")

def seed_gateway():
    import tally_io
    tally_io.COMPANY = COMPANY
    print(f"Seeding company: {COMPANY!r}")
    print("List of Companies bytes:", len(tally_io.export("List of Companies")), "(0 => gateway not reachable)")
    print("\n-- masters (units, ledgers, stock items) --")
    ok = 0
    for m in master_messages():
        st = tally_io.post(envelope("All Masters", [m]))
        ok += 1 if st[0] == "ok" else 0
    print(f"  {ok}/{len(master_messages())} masters posted.")
    for label, batch in (("FY2024-25 reference", REF_2425 + ENRICH_2425), ("FY2025-26 practice", BOOK_2526)):
        ok = 0
        for v in batch:
            st = tally_io.post(envelope("Vouchers", [voucher_msg(*v)]))
            ok += 1 if st[0] == "ok" else 0
            if st[0] != "ok":
                print(f"  !! {v[0]} {st}")
        print(f"-- {label}: {ok}/{len(batch)} vouchers posted.")
    ok = 0  # stock-tracked GST invoices (need F11 Inventory = Yes)
    for v in INV_2425:
        st = tally_io.post(envelope("Vouchers", [inventory_msg(*v)]))
        ok += 1 if st[0] == "ok" else 0
        if st[0] != "ok":
            print(f"  !! {v[0]} {st} (is F11 Inventory = Yes?)")
    print(f"-- FY2024-25 inventory invoices: {ok}/{len(INV_2425)} posted.")
    print()
    _print_expectations()

if __name__ == "__main__":
    if "--company" in sys.argv:
        COMPANY = sys.argv[sys.argv.index("--company") + 1]
    if "--emit" in sys.argv:
        emit_files()
    else:
        seed_gateway()
