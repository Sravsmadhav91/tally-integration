# Getting started for accountants (zero coding assumed)

This toolkit is driven by an **AI coding assistant** (like **Claude Code** or **Google Antigravity**) that
runs on your computer, talks to TallyPrime, and reads your bank statements / PDFs / Excel files. You don't
write code — you *ask*, review, and approve. This page gets your machine ready.

![How it works: you ask in plain English, the AI assistant reads your files and talks to the TallyPrime gateway, and every write waits for your approval](./docs/flow.svg)

## What using it actually looks like (you chat; you don't type commands)
A typical session is a **plain-English conversation**:
> **You:** "Enter the missing ICICI bank transactions for FY25-26 from the statement in `D:\Client\2025-26\`."
> **AI:** reads the statement, compares it to what's already in Tally, and shows you a **table of the entries
> it plans to add** — then asks whether to go ahead.
> **You:** "Looks right — post them."  →  the AI writes them and reads them back to confirm the balances tie.

The `python …` commands you'll see in these docs are what the AI runs **under the hood** — you just ask in
plain English and approve. New words below are in the [Glossary](#glossary-plain-english).

## What you actually need (it's less than you think)

The AI reads most documents **by itself**, so you don't need a big toolchain:

| You need | Why | Skip if… |
|---|---|---|
| **TallyPrime** + an active licence | the books live here; the gateway answers on port 9000 | — (required) |
| **An AI coding assistant** | **Claude Code** or **Google Antigravity** — the thing you talk to (both set up in §1) | — (required) |
| **Python 3** + this repo's `requirements.txt` | runs the helper scripts (import, reconcile, review sheets) | — (required) |
| *Optional power tools* | only for edge cases (see below) | you can add these later, only when a task needs them |

> **The AI already reads images and PDFs.** Claude Code can open a scanned statement, a rent receipt photo,
> or an FD certificate PDF and read it directly — **no OCR software needed** for one-off documents. You only
> reach for extra tools in the specific cases noted below.

## 1. Install the AI assistant (pick ONE)

Any agentic coding tool works — it just needs to read files and run local commands. Then **open this repo's
folder in it** so the AI can see the scripts and docs.

**Option A — Google Antigravity (free; the cheapest way to start, esp. in India).**
- Download from **<https://antigravity.google>** (Windows / Mac / Linux). **Free for individuals** (public
  preview). It's an *agent-first* IDE with an **Agent panel** where the AI plans and runs steps for you.
- Models: **Gemini 3 Pro** with generous free limits (also supports **Claude Sonnet** and others).
- **🇮🇳 India free upgrade:** **Jio** 5G users (₹349+ plan) can claim **18 months of Google AI Pro / Gemini
  free** (worth ₹35,100) — open the **MyJio app → "Google Gemini offer" banner → register with your Gmail**.
  That raises your Gemini limits for heavy use. *(Offer terms as of mid-2026 — verify current eligibility;
  the "18–25 yrs, active 5G plan" conditions change.)*

**Option B — Claude Code (what this toolkit was built and tested with).**
- Easiest: the **Claude desktop app** (Windows/Mac) — no terminal. Or terminal: install **Node.js LTS** from
  <https://nodejs.org>, run `npm install -g @anthropic-ai/claude-code`, then type `claude` in this repo's folder.
- Needs a paid **Claude Pro/Max** plan or an Anthropic **API key**.

**Option C — Cursor / other agentic IDEs** — same repo works; the Tally + Python steps are identical.

## 1a. Turn ON auto / agent mode (important — this is what makes it hands-off)
Plain chat only *suggests*; **agent mode lets the AI actually run the steps** (read your statement → build a
sheet → run a report → reconcile) end-to-end. Enable it:
- **Antigravity:** work in the **Agent panel** (not plain chat) and let the agent **plan + execute**; turn on
  auto-run so it doesn't stop at every action.
- **Claude Code:** use the agent session and **enable auto-accept** — press **Shift+Tab** to cycle to
  *auto-accept edits*, and use **`/permissions`** to allow the read/report/`python` commands so it runs them
  without asking each time.
- **⚠️ The one safety line:** auto-run freely for **reads, reports, dry-runs, and the practice company**. For
  **writing to a REAL book, keep a manual gate** — let the AI dry-run and show the entries, and approve the
  actual write (`--post`) yourself. (The importer is **dry-run-by-default** for exactly this reason.)

## 2. Install Python + the helpers

1. Install **Python 3** from <https://python.org> — on Windows, tick **“Add Python to PATH”** during setup.
2. In this repo's folder, install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   That's `requests`, `pandas`, `openpyxl` — enough for importing, reconciling, and building review sheets.

## 3. Turn on the Tally gateway

Follow [`SETUP.md`](./SETUP.md): TallyPrime → F1 → Settings → Connectivity → *acts as Both*, port **9000**,
company **loaded**. Confirm the licence is **active** (not “Educational mode”, which rejects most dates).

## 4. Optional power tools — add only when a task needs them

Install these individually *if and when* the AI tells you it needs one:

| Tool | Install | Use it only for |
|---|---|---|
| **pymupdf** | `pip install pymupdf` | **password-protected** PDFs (e.g. AIS/TIS, some bank e-statements) and fast bulk text extraction |
| **pdfplumber** | `pip install pdfplumber` | PDFs with **complex tables** the plain read mis-aligns |
| **Tesseract OCR** + `pip install pytesseract pillow` | Windows build: <https://github.com/UB-Mannheim/tesseract/wiki> | **bulk/offline OCR** of many scanned images at once (single scans — just let the AI read them) |
| **pandas** (already installed) | — | comparing two Excel/CSV files, gap-checks, diffs |

Excel comparison and image→text are **not** separate products to buy — they're the AI plus these small
libraries. For a handful of files, the AI's built-in reading is usually all you need.

## 5. Your first 10 minutes

### Step 1 — get this repo onto your computer
The AI assistant works on a **local folder**, so you first need these files on your PC. Pick whichever is easiest:

- **Easiest — let the AI fetch it.** Open Claude Code / Antigravity in any folder and paste:
  > *"Clone the public repo `https://github.com/puneetkeshav/tally-integration` into a folder on my machine,
  > then open it and tell me in plain English what's inside and how to get started."*
  >
  > The assistant runs the download for you and opens the folder. (If it asks permission to run `git`, allow it.)
- **With Git:** run `git clone https://github.com/puneetkeshav/tally-integration.git`, then open that folder in your assistant.
- **No Git? Download the ZIP:** on the [repo page](https://github.com/puneetkeshav/tally-integration) click the
  green **`Code`** button ▸ **Download ZIP**, unzip it, and open the unzipped folder in your assistant.

### Step 2 — one prompt to set everything up
Turn on **agent / auto mode** (§1a), make sure TallyPrime is running with a company loaded, then paste this
**first setup prompt**. It's safe — it only reads and checks; it won't write to any book:

> *"I've opened the tally-integration repo and I'm new to this. I'm on Windows with TallyPrime installed.
> Walk me through setup in plain English, doing each step for me: (1) check Python is installed and install
> this repo's `requirements.txt`; (2) help me switch on the Tally gateway on port 9000 following `SETUP.md`;
> (3) then confirm you can connect and list the companies you can see. Don't write anything to any company —
> reads only."*

### Step 3 — practise safely, then go live
1. **Build the throwaway practice company:** follow [`sample/`](./sample/) → create **`SampleCompany`**
   (or restore the ready-made backup), seed it, and do **Exercise 1** (read it back). Nothing here touches a real client.
2. When comfortable, create a **conventions file** for a real client from
   [`conventions-template.md`](./conventions-template.md), and always work the review-gated flow:
   gap-analyse → review sheet → test-small → bulk (idempotent) → reconcile.

Handy first things to say to the AI: see the [prompt cheat-sheet](./PROMPTS.md).

## Using it on a REAL company (with real data)
**Yes — this is for real books, not just the sandbox** (the toolkit was developed against a live company).
Switching from the practice company to a real one changes nothing in the tools — you just point them at it:
1. **Load your real company** in Tally with the gateway on (`SETUP.md`); tell the AI its exact name.
2. **Create a conventions file** for it from [`conventions-template.md`](./conventions-template.md). The AI
   reads your prior-year entries to learn your ledger names, narration style and posting recipes, so new
   entries look like yours. (One per company; keep it private — it has client data.)
3. **Work the review-gated flow every time:** back up → the AI gap-analyses what's already in Tally → drafts a
   review sheet / dry-run → **you approve** → it posts (idempotent, re-runnable) → it reconciles to the
   statement / 26AS.

Same safeguards as always: **back up before writing, dry-run and approve writes, and leave tax judgement to
your CA.** On a big multi-year book, use `tally_report.py` for balances (it caches once) rather than asking
for live all-ledger balances, which can hang Tally (quirks #5a).

## Safety, always

- **Back up** the company in Tally before any import (Gateway → F3/Alt-Y → Backup).
- **Never** open or edit the binary files under `…\TallyPrime\data\<companyId>\` — go through the gateway.
- **AI drafts, you decide.** Review every batch before it posts; leave tax judgement to your CA.

## Glossary (plain English)
- **AI assistant / agent** — the program you chat with (Claude Code, etc.); it can read your files and run tools on your PC.
- **Gateway** — a small "door" built into TallyPrime that lets other programs read/write the open company (port 9000). You switch it on once (see `SETUP.md`).
- **Voucher** — one entry in Tally (a payment, receipt, journal…). **Ledger** — one account (a bank, a party, an expense head).
- **REMOTEID** — a label the AI stamps on each entry so re-running **updates the same entry instead of duplicating it** (imports are safe to re-run).
- **Dry-run** — a preview: the AI shows what it *would* post, saving nothing, so you can check first. Then you say "post".
- **CLI / command / script** — a typed instruction (`python …`) the AI runs for you; **you don't type these**.
- **Cache** — a temporary local copy of your Tally data the reporting tool pulls once so reports are fast (kept on your PC, never shared).
- **CSV / XLSX** — spreadsheet files (CSV = simple text table; XLSX = Excel).
- **26AS / AIS / TIS** — Income-Tax-department statements of your income & TDS; the AI reconciles the books to these.
- **Educational mode** — Tally with no active licence; it only accepts entries dated the 1st/2nd/last of a month — keep the licence active to avoid confusing errors.
- **Gap-analysis** — before writing, the AI checks what's *already* in Tally and only adds what's missing (so nothing doubles up).
