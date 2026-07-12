<!-- Thanks for contributing! Please fill this in so reviewers can move fast. -->

## What does this change?

<!-- One or two sentences. Link any related issue: "Fixes #12" -->

## How did you test it?

<!-- Did you run it against the sample/ practice company? Which report/script/exercise? -->

- [ ] Tested against the **sample company** (not a real book)
- [ ] Docs updated if behaviour changed (quirks.md / PROMPTS.md / scripts/README.md / sample/)

## Checklist

- [ ] **No real client or personal data** (no real PAN / account numbers / GSTIN / names / company files)
- [ ] **Company-agnostic** — nothing hard-codes a real company; per-company logic stays in a private
      conventions file
- [ ] Any **write path keeps the review gate** (dry-run / preview before posting)
- [ ] Doesn't introduce whole-book live-balance queries that can hang Tally (quirks #5a)
