"""
tally_io.py — reusable, config-driven helpers for the TallyPrime HTTP-XML gateway.

Generic building blocks distilled from real FY-close work. No client data here — set COMPANY
and your ledger map, then use export()/post_voucher()/journal(). See README.md for the safe workflow.

Requires: requests  (pip install requests). Python 3.8+.
"""
import re, time, requests
from xml.sax.saxutils import escape

URL = "http://localhost:9000"
COMPANY = "YOUR COMPANY NAME"            # <-- must match the loaded company verbatim

# ---------------------------------------------------------------- exports (read)
def export(report_id, fromdate=None, todate=None, extra_sv=""):
    """Export a Tally report as XML. report_id e.g. 'Voucher Register', 'Trial Balance',
       'Profit and Loss', 'List of Accounts'. Dates as 'YYYYMMDD'."""
    sv = f"<SVCURRENTCOMPANY>{escape(COMPANY)}</SVCURRENTCOMPANY><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"
    if fromdate: sv += f"<SVFROMDATE>{fromdate}</SVFROMDATE>"
    if todate:   sv += f"<SVTODATE>{todate}</SVTODATE>"
    sv += extra_sv
    x = (f"<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE>"
         f"<ID>{escape(report_id)}</ID></HEADER><BODY><DESC><STATICVARIABLES>{sv}"
         f"</STATICVARIABLES></DESC></BODY></ENVELOPE>")
    return requests.post(URL, data=x.encode("utf-8"), headers={"Content-Type": "text/xml"}, timeout=60).text

# ---------------------------------------------------------------- writes (import)
def _leg(ledger, drcr, amount):
    """One accounting leg. drcr: 'Dr' or 'Cr'. amount: positive number."""
    dp = "Yes" if drcr == "Dr" else "No"
    amt = -amount if drcr == "Dr" else amount   # quirks #17: Dr = negative, Cr = positive
    return (f"<ALLLEDGERENTRIES.LIST><LEDGERNAME>{escape(ledger)}</LEDGERNAME>"
            f"<ISDEEMEDPOSITIVE>{dp}</ISDEEMEDPOSITIVE><AMOUNT>{amt:.2f}</AMOUNT></ALLLEDGERENTRIES.LIST>")

def build_voucher(remoteid, vtype, date, narration, legs):
    """legs: list of (ledger, 'Dr'/'Cr', positive_amount). vtype: Payment/Receipt/Contra/Journal.
       Asserts the voucher balances (sum of signed legs == 0)."""
    signed = sum((-a if dc == "Dr" else a) for _, dc, a in legs)
    assert abs(signed) < 0.005, f"unbalanced voucher {remoteid}: {signed}"
    body = "".join(_leg(l, dc, a) for l, dc, a in legs)
    vch = (f'<VOUCHER REMOTEID="{escape(remoteid)}" VCHTYPE="{vtype}" ACTION="Create" '
           f'OBJVIEW="Accounting Voucher View"><DATE>{date}</DATE><EFFECTIVEDATE>{date}</EFFECTIVEDATE>'
           f'<VOUCHERTYPENAME>{vtype}</VOUCHERTYPENAME><NARRATION>{escape(narration)}</NARRATION>{body}</VOUCHER>')
    return (f'<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA>'
            f'<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES>'
            f'<SVCURRENTCOMPANY>{escape(COMPANY)}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC>'
            f'<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">{vch}</TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>')

def post(xml, attempts=6):
    """POST one import envelope with retry on the transient 'retry Split'. Returns (status, created, altered)."""
    resp = ""
    for _ in range(attempts):
        try:
            resp = requests.post(URL, data=xml.encode("utf-8"), headers={"Content-Type": "text/xml"}, timeout=60).text
        except Exception:
            time.sleep(0.6); continue
        c = int((re.search(r"<CREATED>(\d+)", resp) or [0, 0])[1])
        a = int((re.search(r"<ALTERED>(\d+)", resp) or [0, 0])[1])
        ex = int((re.search(r"<EXCEPTIONS>(\d+)", resp) or [0, 0])[1])
        if (c + a) > 0 and ex == 0:
            return ("ok", c, a)
        time.sleep(0.6)   # transient/licence-jam back-off (quirks #2, #11)
    le = re.search(r"<LINEERROR>(.*?)</LINEERROR>", resp)
    return ("fail", le.group(1)[:80] if le else resp[:80], 0)

def journal(remoteid, date, legs, narration):
    """Post a Journal voucher. legs: list of (ledger,'Dr'/'Cr',amount)."""
    return post(build_voucher(remoteid, "Journal", date, narration, legs))

def delete_voucher(remoteid, vtype, date):
    """Delete a voucher by its externally-set REMOTEID (quirks #12)."""
    x = (f'<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA>'
         f'<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES>'
         f'<SVCURRENTCOMPANY>{escape(COMPANY)}</SVCURRENTCOMPANY></STATICVARIABLES></REQUESTDESC>'
         f'<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">'
         f'<VOUCHER REMOTEID="{escape(remoteid)}" VCHTYPE="{vtype}" ACTION="Delete">'
         f'<DATE>{date}</DATE><VOUCHERTYPENAME>{vtype}</VOUCHERTYPENAME></VOUCHER>'
         f'</TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>')
    r = requests.post(URL, data=x.encode("utf-8"), headers={"Content-Type": "text/xml"}, timeout=60).text
    return int((re.search(r"<DELETED>(\d+)", r) or [0, 0])[1])

if __name__ == "__main__":
    # connectivity + licence smoke test (safe: creates then deletes a Re.1 test on the 1st of a month)
    print("List of Companies bytes:", len(export("List of Companies")))
    print("Set COMPANY + a real ledger map, then use export()/journal()/post(). See README.md.")
