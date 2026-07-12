# Ready-made practice company (Tally backup)

The fastest way to get the sandbox: **restore** the pre-built company instead of importing XML.

> **Why a backup, not raw data files?** A Tally company on disk is a set of **binary files** you must never
> hand-edit (see the toolkit's golden rules). The only safe, portable, shareable form is Tally's **own
> Backup**, produced by Tally and restored by Tally. That's what lives here:
>
> - **[`TBK1800_100000.001`](./TBK1800_100000.001)** — the backup **data** (company **`SampleCompany`**).
>
> ⚠️ **Manifest file:** a Tally backup usually also writes a small companion manifest (e.g.
> `TBK1800.900` / `TBK1800_100000.900`) in the same output folder. If your TallyPrime's **Restore** doesn't
> list `SampleCompany` from the data file alone, you also need that `.900` file — copy it from the folder you
> backed up to, into the same folder as the `.001`. (If Restore *does* find the company, you're set.)

## Restore it (2 minutes)

1. Copy **`TBK1800_100000.001`** (and the `.900` manifest, if your Tally needs it — see above) from this
   folder into any empty folder, e.g. `C:\TallyPractice\`.
2. TallyPrime → **Alt-F3** (Company) → **Restore**.
3. Set **Source** to that folder and **Destination** to your normal Tally data path (e.g.
   `C:\Users\Public\TallyPrime\data`). Accept.
4. Pick **`SampleCompany`** from the list, restore, then **load** it and enable the gateway
   (see [`../../SETUP.md`](../../SETUP.md)).

You now get the same two years as the XML/seed route — **Practice Bank opening ₹2,94,200**, the correct
FY24-25 reference year (multi-bank, GST, TDS, loans, stock invoices) and the flawed FY25-26 practice year.
Go to [`../README.md`](../README.md) for Lesson 0, the TDS/capital-gains lessons, and the exercises.

> **Version note:** this backup was taken from **TallyPrime 6.1** (data level 1800). A backup restores in the
> **same major version or newer** — so **TallyPrime 6.1 or later** opens it directly. On an **older**
> TallyPrime it won't restore; fall back to the XML import (route B) or the seed script (route A) in
> [`../README.md`](../README.md) — both are version-neutral.

## Producing / refreshing the backup (maintainers)

The binary can't be generated programmatically — it must come out of Tally itself. To (re)create it:

1. In Tally, **Create Company** named `SampleCompany` (set **Financial year beginning = 1-Apr-2024** so both
   years fit); load it; enable the gateway.
2. Seed it: `python ../seed_practice_data.py --company "SampleCompany"`  (or import `../practice_masters.xml`,
   then `../practice_vouchers_2024-25.xml`, then `../practice_vouchers_2025-26.xml`).
3. Verify (day book / trial balance) it matches [`../ANSWERS.md`](../ANSWERS.md).
4. Gateway of Tally → **Alt-F3** → **Backup**; choose an empty output folder.
5. Copy the resulting **`TBK*.001`** (and the **`TBK*.900`** manifest) into this folder and commit them;
   update the filename(s) + version note above.

> **Before committing any backup, confirm it holds ONLY the synthetic sample** (no real company data) — a
> backup here is published publicly. Quick check: extract printable strings and confirm you see the sample
> ledgers (`Practice Bank`, `Widget`, `Vendor XYZ`…) and **no** real client/bank names.
