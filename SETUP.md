# Setup — enable the Tally gateway & connect (5 minutes)

The toolkit talks to TallyPrime over its built-in HTTP-XML gateway. No add-on, no cloud — it's all local.

## 1. Turn on the gateway in TallyPrime
1. Open **TallyPrime** and **load the company** you'll work on (the gateway only answers for a loaded company).
2. Press **F1 → Settings → Connectivity** (older builds: `F12 → Advanced Configuration`).
3. Set **TallyPrime acts as → Both** (or *Server*), **Enable ODBC/Port**, **Port = 9000**.
4. Accept and keep TallyPrime running. The window title bar should show it's listening (not "Educational").

## 2. Confirm the licence is ACTIVE (important)
If Tally is in **Educational mode** (no licence), imports are rejected for any date that isn't the
**1st, 2nd, or last day of a month** — with a misleading "Voucher date is missing" error (see `quirks.md` #2a).
Check the bottom of the Tally window shows your serial, not "Educational".

## 3. Test connectivity
```bash
# list companies (works even before a company is loaded)
curl.exe -s -X POST -H "Content-Type: text/xml" --data-binary @examples/01-list-companies.xml http://localhost:9000
```
You should get an XML list of companies. If you get nothing / connection refused: gateway isn't on, port
differs, or Tally isn't running. If you get `Could not set 'SVCurrentCompany'`: the company isn't loaded.

## 4. Python helpers (optional but recommended)
```bash
pip install -r requirements.txt          # requests, pandas, openpyxl
# then, in scripts/tally_io.py, set COMPANY = "Your Company Name" (verbatim)
python scripts/tally_io.py               # prints a connectivity smoke test
```

## 5. Safety first (every time you write)
- **Back up** the company in-app (Gateway of Tally → F3/Alt-Y → Backup) before any import.
- Read `quirks.md` once — it will save you hours.
- Follow the review-gated workflow in `scripts/README.md`: gap-analyse → review sheet → test-small →
  bulk (idempotent REMOTEID) → reconcile.

## Want to practise without touching real books?
See [`sample/`](./sample/) — create a throwaway company and seed it with sample data, then run the toolkit
against it.
