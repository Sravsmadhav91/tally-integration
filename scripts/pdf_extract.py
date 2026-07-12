"""
pdf_extract.py -- dump TEXT or TABLES from a (possibly password-protected) PDF, to help turn a source
document (bank statement, invoice, 26AS/AIS, Form-16, interest certificate) into a structured sheet.

WHEN TO USE THIS vs just letting the AI read the PDF:
  * Prefer letting your AI assistant read the PDF directly (its Read tool handles PDFs/images via vision) —
    that copes with odd layouts and scans better than any generic parser.
  * Use THIS helper for the cases the AI can't do directly: **password-protected** PDFs (26AS/AIS/Form-16)
    and **bulk/repeatable** extraction where you want raw text/tables in a file.

USAGE
  python pdf_extract.py --file statement.pdf                          # text to stdout
  python pdf_extract.py --file AIS.pdf --password aaaaa1111a01011990  # unlock, then text (PAN-lc + DOB)
  python pdf_extract.py --file bank.pdf --pages 1-3 --out bank.txt    # text of pages 1-3 to a file
  python pdf_extract.py --file invoice.pdf --tables --out lines.csv   # extract tables to CSV (pdfplumber)

Password note: Indian tax-portal PDFs are usually **PAN in lowercase + DOB DDMMYYYY** (e.g. aaaaa1111a01011990).
Deps (optional power tools): pymupdf (text + unlock), pdfplumber (tables). See requirements-optional.txt.

ALWAYS prove the extraction is complete before feeding a sheet to import_sheet.py (quirks #37):
  * BEST — the RUNNING BALANCE: if the source prints one (bank statements do), recompute it from the opening
    balance + each extracted line and match the printed running balance ROW BY ROW — this pinpoints the exact
    row where a line was missed/duplicated/mis-keyed (a grand total can hide two offsetting errors).
  * else tie to the control figures the doc prints: total debits, total credits, closing balance, txn count.
"""
import sys, argparse, csv

def page_range(spec, n):
    if not spec:
        return range(n)
    if "-" in spec:
        a, b = spec.split("-", 1)
        return range(int(a) - 1, min(int(b), n))
    return range(int(spec) - 1, int(spec))

def extract_text(path, password, pages):
    try:
        import fitz  # pymupdf
    except ImportError:
        raise SystemExit("pymupdf not installed — `pip install pymupdf` (see requirements-optional.txt).")
    doc = fitz.open(path)
    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            raise SystemExit("PDF is password-protected — pass the right --password "
                             "(tax PDFs: PAN-lowercase + DOB DDMMYYYY).")
    out = []
    for i in page_range(pages, doc.page_count):
        out.append(f"----- page {i + 1} -----")
        out.append(doc[i].get_text())
    return "\n".join(out)

def extract_tables(path, password, pages):
    try:
        import pdfplumber
    except ImportError:
        raise SystemExit("pdfplumber not installed — `pip install pdfplumber` (see requirements-optional.txt).")
    rows = []
    with pdfplumber.open(path, password=password) as pdf:
        for i in page_range(pages, len(pdf.pages)):
            for t in (pdf.pages[i].extract_tables() or []):
                rows.extend(t)
                rows.append([])  # blank line between tables
    return rows

def main():
    ap = argparse.ArgumentParser(description="Dump text/tables from a PDF (handles passwords).")
    ap.add_argument("--file", required=True)
    ap.add_argument("--password")
    ap.add_argument("--pages", help='e.g. "1-3" or "2" (1-indexed)')
    ap.add_argument("--tables", action="store_true", help="extract tables (pdfplumber) instead of text")
    ap.add_argument("--out", help="write to this file instead of stdout (.csv for --tables)")
    a = ap.parse_args()
    if a.tables:
        rows = extract_tables(a.file, a.password, a.pages)
        if a.out:
            with open(a.out, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
            print(f"wrote {a.out} ({len(rows)} rows). VERIFY: recompute the running balance (or tie to control totals) before importing.")
        else:
            for r in rows:
                print(",".join("" if c is None else str(c).replace("\n", " ") for c in r))
    else:
        text = extract_text(a.file, a.password, a.pages)
        if a.out:
            open(a.out, "w", encoding="utf-8").write(text)
            print(f"wrote {a.out} ({len(text)} chars). VERIFY: recompute the running balance (or tie to control totals) before importing.")
        else:
            print(text)

if __name__ == "__main__":
    main()
