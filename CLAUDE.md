# CLAUDE.md — instructions for Claude Code in this repo

Your full standing brief is **@AGENTS.md** — read it. The essentials:

- **AI drafts, the human decides.** Reads and reports run freely; **dry-run and get explicit approval before
  writing to any real book.** Never post to a real company unprompted; have the user back up first.
- **Never fetch all-ledger balances live** — it can hang Tally's single-threaded gateway (quirks #5a). Use
  `scripts/tally_report.py` (cached SQL). Talk to Tally only via the gateway (`localhost:9000`); never touch
  the binary company files.
- **No real client data in the repo.** Practise against `SampleCompany` in `sample/`; a real client's
  specifics go in a private file made from `conventions-template.md`.
- The user is often a **non-coder** — explain in plain English and do the steps for them.

See **@AGENTS.md** for the gateway rules, the data-entry workflow, the quirks to read first, and the file map.
