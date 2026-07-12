# Screenshots

Drop real screenshots here to make the docs friendlier for first-time users. They can't be auto-generated
(they're of the AI-assistant and TallyPrime windows on *your* machine), so this is a quick capture checklist.
Once a file exists here, it gets embedded in the doc named beside it.

> **How to capture (Windows):** press **Win + Shift + S** (Snipping Tool), drag over the window, then paste
> into any image file or save directly. Save as **PNG** with the exact filename below.
>
> ⚠️ **Blur/redact anything real** — company names, PANs, account numbers, amounts — before saving.
> Best practice: take every screenshot against the **`SampleCompany`** practice company, which has no real data.

| Filename to save | What it should show | Used in |
|---|---|---|
| `antigravity-agent.png` | Google Antigravity with the **Agent panel** open (a task running) | `ENVIRONMENT.md` §1 / §1a |
| `claude-code.png` | Claude Code mid-session (a prompt + the AI's plan/response) | `ENVIRONMENT.md` §1 / §1a |
| `auto-mode.png` | The **auto/agent mode** turned on (Antigravity auto-run, or Claude Code's auto-accept indicator) | `ENVIRONMENT.md` §1a |
| `first-setup.png` | The result of the **first setup prompt** — the AI listing your companies over the gateway | `ENVIRONMENT.md` §5 |
| `bank-recon.png` | A **bank reconciliation** result (mismatched dates + the gap), e.g. the sample's `bank-recon` report | `README.md` "See it in action" |
| `dry-run-approve.png` | A **dry-run preview** of entries the AI is about to post (the review gate) | `README.md` / `ENVIRONMENT.md` |

When you've added one, tell the assistant "wire up the screenshots" and it will insert the `![...](...)`
image tags at the right spots. Keep images reasonably small (< ~300 KB each; resize/compress if larger).
