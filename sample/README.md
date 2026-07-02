# Practice sandbox

Learn the toolkit against a **throwaway company** — never practise on a real client's books.

## Set up (2 minutes)
1. In **TallyPrime → Create Company**, name it exactly **`Tally AI Practice`** (any address; keep defaults).
2. Load it and enable the gateway on port 9000 (see [`../SETUP.md`](../SETUP.md)).
3. Seed it:
   ```bash
   pip install requests
   python seed_practice_data.py
   ```
   This creates 8 ledgers and 8 sample vouchers (Receipt/Payment/Contra/Journal). All dates are the
   1st/2nd/last of a month, so it works **even without a licence** (Educational mode).

## Exercises (do these with the toolkit)
1. **Read it back.** Export the day book / voucher register and confirm your 8 vouchers are there:
   ```bash
   curl.exe -s -X POST -H "Content-Type: text/xml" --data-binary @../examples/03-read-daybook.xml http://localhost:9000
   ```
2. **Trial balance & P&L.** Use `../examples/12-export-trial-balance.xml` and `13-export-profit-loss.xml`
   (edit the company name to `Tally AI Practice`). Confirm Consulting Income = ₹1,35,000, expenses tie out.
3. **Reconcile a "bank statement".** Take Practice Bank's vouchers as your "book", invent a small CSV of
   "statement" lines (add one line the book is missing), and write a gap-check that finds the missing line
   **by net daily movement** (not per-line — see quirks #22). Import the missing one with a `REMOTEID`.
4. **Idempotency.** Re-run `seed_practice_data.py` — note everything reports **altered**, nothing duplicates.
5. **Reverse.** Delete one seeded voucher via its REMOTEID (`../examples/11-delete-voucher.xml`, set
   `REMOTEID="SEED-PAY-03"`), re-read, confirm it's gone. Re-seed to restore.
6. **Book a year-end journal.** Post an accrual with `tally_io.journal(...)` and reconcile the P&L change.

## Clean up
Delete the `Tally AI Practice` company in Tally when done (Gateway → Alt-F3 → Delete), or keep it as a scratchpad.
