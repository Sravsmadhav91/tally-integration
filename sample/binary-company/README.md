# Ready-made practice company (Tally backup)

The fastest way to get the sandbox: **restore** a pre-built company instead of importing XML.

> **Why a backup, not raw data files?** A Tally company on disk is a set of **binary files** you must never
> hand-edit (see the toolkit's golden rules). The only safe, portable, shareable form is Tally's **own
> Backup** (`TBK900.001` + `TBK900.900`), produced by Tally and restored by Tally. That's what lives here.

## Restore it (2 minutes)

1. Copy the two `TBK900.*` files from this folder into any empty folder, e.g. `C:\TallyPractice\`.
2. TallyPrime → **Alt-F3** (Company) → **Restore**.
3. Set **Source** to that folder and **Destination** to your normal Tally data path. Accept.
4. Load **`Tally AI Practice`** and enable the gateway (see [`../../SETUP.md`](../../SETUP.md)).

You now have the same two years (16 ledgers, 42 correct FY24-25 vouchers + 9 flawed FY25-26 vouchers) as
the XML/seed route. Go to [`../README.md`](../README.md) for Lesson 0 and the exercises.

## Producing / refreshing the backup (maintainers)

The binary can't be generated programmatically — it must come out of Tally itself. To (re)create it:

1. In Tally, **Create Company** (set **Financial year beginning = 1-Apr-2024** so both years fit); load it; enable the gateway.
2. Seed it: `python ../seed_practice_data.py --company "Your Name"`  (or import `../practice_masters.xml`,
   then `../practice_vouchers_2024-25.xml`, then `../practice_vouchers_2025-26.xml`).
3. Verify (day book / trial balance) it matches [`../ANSWERS.md`](../ANSWERS.md).
4. Gateway of Tally → **Alt-F3** → **Backup**; choose an empty output folder.
5. Copy the resulting **`TBK900.001`** and **`TBK900.900`** into this folder and commit them.

> **Version note:** a restored backup must be opened in the same **major** TallyPrime version (or newer) it
> was taken from. Note your Tally version here when you commit the files. If a user's version can't restore
> it, they should fall back to the XML import (route B) or the seed script (route A) — both are version-neutral.

*(The `TBK900.*` files are intentionally not checked in yet — a maintainer with a licensed Tally generates
them per the steps above.)*
