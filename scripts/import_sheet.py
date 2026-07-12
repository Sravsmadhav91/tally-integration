"""
import_sheet.py -- post vouchers to Tally from a reviewed Excel/CSV. **Dry-run by default.**

This is the review-gated bulk-import step: a human (or the AI) prepares/reviews a sheet, you dry-run it to
see the balanced vouchers, then --post. Idempotent (REMOTEID) so it's safely re-runnable.

SHEET SCHEMA (one row per ledger LEG; rows sharing a remoteid = one voucher):
  remoteid | date | vtype | ledger | drcr | amount | narration
  - date      : DD-MM-YYYY, YYYY-MM-DD, or YYYYMMDD
  - vtype     : Payment | Receipt | Contra | Journal   (simple ledger vouchers)
  - ledger    : exact ledger name (copy verbatim)
  - drcr      : Dr | Cr
  - amount    : positive number
  - narration : optional; the first non-empty value in the group is used
  (Inventory/GST *item invoices* are NOT handled here — they need Invoice Voucher View; see the sample seed.)

USAGE
  python import_sheet.py --company "My Co" --file vouchers.csv            # dry-run: validate + preview
  python import_sheet.py --company "My Co" --file vouchers.xlsx --sheet Sheet1
  python import_sheet.py --company "My Co" --file vouchers.csv --post     # actually post

Deps: requests (via tally_io); openpyxl only for .xlsx.
"""
import sys, os, re, csv, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tally_io

REQUIRED = ["remoteid", "date", "vtype", "ledger", "drcr", "amount"]

def norm_date(s):
    s = str(s).strip()
    if re.fullmatch(r"\d{8}", s):
        return s
    m = re.match(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", s)          # DD-MM-YYYY
    if m:
        return f"{m.group(3)}{int(m.group(2)):02d}{int(m.group(1)):02d}"
    m = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", s)          # YYYY-MM-DD
    if m:
        return f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}"
    raise ValueError(f"unrecognised date {s!r} (use DD-MM-YYYY / YYYY-MM-DD / YYYYMMDD)")

def norm_drcr(s):
    s = str(s).strip().lower()
    if s.startswith("d"):
        return "Dr"
    if s.startswith("c"):
        return "Cr"
    raise ValueError(f"drcr must be Dr/Cr, got {s!r}")

def read_rows(path, sheet):
    if path.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb[sheet] if sheet else wb.active
        grid = [[c.value for c in r] for r in ws.iter_rows()]
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            grid = list(csv.reader(f))
    grid = [r for r in grid if any(str(c).strip() for c in r if c is not None)]
    if not grid:
        raise SystemExit("empty sheet")
    hdr = [str(h).strip().lower() for h in grid[0]]
    missing = [c for c in REQUIRED if c not in hdr]
    if missing:
        raise SystemExit(f"sheet is missing required column(s): {missing}; has {hdr}")
    return [{hdr[i]: (row[i] if i < len(row) else None) for i in range(len(hdr))} for row in grid[1:]]

def group_vouchers(rows):
    order, by_id = [], {}
    for r in rows:
        rid = str(r["remoteid"]).strip()
        if rid not in by_id:
            by_id[rid] = {"remoteid": rid, "date": None, "vtype": None, "narration": "", "legs": []}
            order.append(rid)
        v = by_id[rid]
        v["date"] = v["date"] or norm_date(r["date"])
        v["vtype"] = v["vtype"] or str(r["vtype"]).strip()
        if not v["narration"] and r.get("narration"):
            v["narration"] = str(r["narration"]).strip()
        v["legs"].append((str(r["ledger"]).strip(), norm_drcr(r["drcr"]), abs(float(str(r["amount"]).replace(",", "")))))
    return [by_id[i] for i in order]

def balanced(v):
    dr = sum(a for _, dc, a in v["legs"] if dc == "Dr")
    cr = sum(a for _, dc, a in v["legs"] if dc == "Cr")
    return abs(dr - cr) < 0.005, dr, cr

def main():
    ap = argparse.ArgumentParser(description="Post vouchers from a reviewed Excel/CSV (dry-run by default).")
    ap.add_argument("--company", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--sheet")
    ap.add_argument("--post", action="store_true", help="actually post (otherwise dry-run)")
    a = ap.parse_args()
    tally_io.COMPANY = a.company
    vouchers = group_vouchers(read_rows(a.file, a.sheet))

    bad = [v for v in vouchers if not balanced(v)[0]]
    print(f"{len(vouchers)} vouchers parsed; {len(bad)} unbalanced.")
    for v in vouchers:
        ok, dr, cr = balanced(v)
        legs = " / ".join(f"{dc} {ld} {amt:,.2f}" for ld, dc, amt in v["legs"])
        flag = "OK " if ok else "*** UNBALANCED (Dr %.2f != Cr %.2f)" % (dr, cr)
        print(f"  [{flag}] {v['remoteid']:26} {v['date']} {v['vtype']:8} | {legs}")
    if bad:
        print("\nFix the unbalanced voucher(s) before posting.")
        if a.post:
            raise SystemExit("aborting --post because of unbalanced vouchers.")
    if not a.post:
        print("\nDRY RUN — nothing posted. Re-run with --post to write these to Tally.")
        return
    print("\nPosting...")
    ok = 0
    for v in vouchers:
        legs = [(ld, dc, amt) for ld, dc, amt in v["legs"]]
        st = tally_io.post(tally_io.build_voucher(v["remoteid"], v["vtype"], v["date"], v["narration"], legs))
        ok += 1 if st[0] == "ok" else 0
        print(f"  {v['remoteid']:26} {st}")
    print(f"\n{ok}/{len(vouchers)} posted (idempotent — re-running ALTERs, never duplicates).")

if __name__ == "__main__":
    main()
