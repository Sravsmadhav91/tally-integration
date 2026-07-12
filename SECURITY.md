# Security & data privacy

This toolkit reads and writes **real financial books**. Please treat it accordingly.

## Never commit real data

- No real **PANs, Aadhaar, account numbers, GSTINs, phone numbers, emails, client/company names**, or
  exported Tally company files in issues, PRs, or commits.
- The local cache (`scripts/.cache/*.sqlite`) contains real book data and is **git-ignored** — keep it that
  way; never force-add it.
- Password-protected source docs (26AS/AIS/Form-16) and their passwords must **never** appear in the repo.
  The example password in the docs is deliberately fake.

## Reporting a vulnerability or a data exposure

If you find a security issue, or notice real data has been committed anywhere in this repo:

- **Do not open a public issue** with the details.
- Instead, open a **minimal** private report — a GitHub Security Advisory
  (`Security` tab → *Report a vulnerability*), or contact the maintainer directly.
- If real data is already public in the history, say so immediately (no details in the clear) so it can be
  purged and, if the data is live (tokens/passwords), rotated.

## Operating safely

- Talk to Tally only through the **HTTP-XML gateway** (`localhost:9000`) — never read/modify the binary
  company files.
- Keep the gateway bound to **localhost**; don't expose port 9000 to the network.
- Every write path keeps a **human-review gate** (dry-run / preview → approve → post). Don't remove it.
- Back up the company in-app before any bulk write.
