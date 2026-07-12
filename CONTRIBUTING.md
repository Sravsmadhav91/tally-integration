# Contributing

Thanks for wanting to help! This toolkit is for accountants and developers who use **TallyPrime + an AI
assistant** to do bookkeeping safely. Contributions of all sizes are welcome — a fixed typo, a new quirk
you discovered, a report, or a whole workflow.

## Ground rules (read these first)

1. **No client / personal data — ever.** No real PANs, account numbers, GSTINs, phone numbers, emails,
   client names, or exported company files. Use the [`sample/`](./sample/) practice company for anything
   that needs data. PRs containing real data will be closed.
2. **Company-agnostic.** Nothing in the repo (except your own local, git-ignored files) may be tied to one
   real company. Per-company logic belongs in a private file made from
   [`conventions-template.md`](./conventions-template.md), not here.
3. **Reads are safe; writes are gated.** Any code that *writes* to a book must keep the human-review gate:
   dry-run / preview first, then post on approval. Don't add a "just post everything" path.
4. **Don't hang Tally.** The gateway is single-threaded — whole-book balance collections can freeze it
   (see [`quirks.md`](./quirks.md) #5/#5a). New readers should go through the cached SQL layer
   (`scripts/tally_report.py`) rather than hammering live-balance queries.

## How to contribute

1. **Fork** the repo and create a branch: `git checkout -b my-change`.
2. Make your change. If it's code, test it against the **sample company** (seed it — see
   [`sample/README.md`](./sample/README.md)) so you're not touching a real book.
3. Keep the docs in sync — new trap → add to `quirks.md`; new prompt → `PROMPTS.md`; new report →
   `scripts/reports/` + a line in `scripts/README.md`.
4. **Open a Pull Request** (see the template that appears). Describe what changed and how you tested it.

You don't need write access to contribute — **fork + PR** is the normal path for a public repo. Maintainers
review and merge.

## Good first contributions

- A new **quirk** you hit (with the exact symptom + fix).
- A new **ready-made report** — drop a `.sql` file in [`scripts/reports/`](./scripts/reports/).
- A **plain-English prompt** that worked well, added to [`PROMPTS.md`](./PROMPTS.md).
- Improving the **beginner onboarding** in [`ENVIRONMENT.md`](./ENVIRONMENT.md).
- A **new sample exercise** in [`sample/`](./sample/) (with its answer in `ANSWERS.md`).

## Reporting bugs / asking questions

Open an **Issue** (templates provided). For anything security- or data-privacy-sensitive, don't post
details publicly — see [`SECURITY.md`](./SECURITY.md).

## Style

- Python: standard library first; keep helpers config-driven and small. Match the surrounding style.
- Docs: plain English, short lines, link generously between files.
- Windows-friendly: examples should work in PowerShell and Git Bash where possible.
