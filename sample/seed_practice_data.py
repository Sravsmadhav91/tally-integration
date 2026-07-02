"""
seed_practice_data.py — populate a THROWAWAY TallyPrime company with sample masters + vouchers
so you can practise the toolkit safely (never run this against a real client's company).

Steps:
  1. In TallyPrime, create a new company named exactly:  Tally AI Practice
  2. Load it, enable the gateway on port 9000 (see ../SETUP.md).
  3. pip install requests ; then:  python seed_practice_data.py
  4. Practise: read it back, reconcile, add/delete vouchers (see README.md exercises).

All voucher dates are the 1st / 2nd / last day of a month, so this seeds even WITHOUT an active
licence (Educational mode; see ../quirks.md #2a). Idempotent — re-running ALTERs, never duplicates.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import tally_io
tally_io.COMPANY = "Tally AI Practice"     # must match the company you created, verbatim

def master_ledger(name, parent):
    x = (f'<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA>'
         f'<REQUESTDESC><REPORTNAME>All Masters</REPORTNAME><STATICVARIABLES>'
         f'<SVCURRENTCOMPANY>{tally_io.COMPANY}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC>'
         f'<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">'
         f'<LEDGER NAME="{name}" ACTION="Create"><NAME>{name}</NAME><PARENT>{parent}</PARENT></LEDGER>'
         f'</TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>')
    return tally_io.post(x)

LEDGERS = [
    ("Practice Bank",     "Bank Accounts"),
    ("Practice Bank 2",   "Bank Accounts"),
    ("Client ABC",        "Sundry Debtors"),
    ("Vendor XYZ",        "Sundry Creditors"),
    ("Consulting Income", "Indirect Incomes"),
    ("Office Rent",       "Indirect Expenses"),
    ("Bank Charges",      "Indirect Expenses"),
    ("Drawings",          "Capital Account"),
]
# (remoteid, vtype, date[1st/2nd/last], narration, legs[(ledger,Dr/Cr,amount)])
VOUCHERS = [
    ("SEED-REC-01","Receipt","20250401","Consulting fee - Client ABC",
        [("Consulting Income","Cr",60000),("Practice Bank","Dr",60000)]),
    ("SEED-PAY-01","Payment","20250402","Office rent April",
        [("Office Rent","Dr",25000),("Practice Bank","Cr",25000)]),
    ("SEED-CON-01","Contra","20250430","Transfer to Bank 2",
        [("Practice Bank 2","Dr",20000),("Practice Bank","Cr",20000)]),
    ("SEED-PAY-02","Payment","20250501","Bank charges + drawings",
        [("Bank Charges","Dr",236),("Drawings","Dr",15000),("Practice Bank","Cr",15236)]),
    ("SEED-REC-02","Receipt","20250502","Consulting fee - Client ABC",
        [("Consulting Income","Cr",45000),("Practice Bank","Dr",45000)]),
    ("SEED-JRN-01","Journal","20250531","Accrue May consulting (billed, not received)",
        [("Client ABC","Dr",30000),("Consulting Income","Cr",30000)]),
    ("SEED-REC-03","Receipt","20250602","Client ABC clears May accrual",
        [("Client ABC","Cr",30000),("Practice Bank","Dr",30000)]),
    ("SEED-PAY-03","Payment","20250602","Vendor XYZ purchase",
        [("Vendor XYZ","Dr",18000),("Practice Bank","Cr",18000)]),
]

if __name__ == "__main__":
    print(f"Seeding company: {tally_io.COMPANY!r}")
    print("List of Companies bytes:", len(tally_io.export("List of Companies")), "(0 => gateway not reachable)")
    print("\n-- ledgers --")
    for n, p in LEDGERS:
        print(f"  {n:20} {master_ledger(n, p)}")
    print("\n-- vouchers --")
    ok = 0
    for rid, vt, dt, nar, legs in VOUCHERS:
        st = tally_io.post(tally_io.build_voucher(rid, vt, dt, nar, legs))
        ok += 1 if st[0] == "ok" else 0
        print(f"  {rid:14} {vt:8} {dt}  {st}")
    print(f"\n{ok}/{len(VOUCHERS)} vouchers posted. Now try the exercises in README.md.")
