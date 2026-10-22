# Promoting literal results to BITS

Owner direction (2026-10-21): keep iterating on the literal and readable sets, publish
only impressive results to BITS at 6, 7 and 8 bits, and remove superseded profiles
from the BITS picker. This rule decides "impressive" and "superseded" before results
are seen. It does not change [M1-M6](MILESTONES.md) or any frozen experiment gate.

## Slots

A BITS slot is one language, one problem cohort (an exact ID set), one width
(6, 7 or 8 bits of payload plus BITS's frame bit), one policy (literal
compression, or readable/human-composed) and one entry category (primitive or macro,
below). Each slot shows at most one current profile.

## Macro category

An entry that contains a complete function or class definition (a JavaScript function,
class or block-bodied arrow that closes inside the entry, or a Python def/class with a
complete body line) is a macro entry: one selection replaces a whole helper. A profile or
set with any macro entry is in the macro category. Macro-category results are reported
separately and are never compared with, used as the bar for, or ranked against
primitive vocabularies. The classifier is 256one `scripts/report-macro-entries.mjs`; its
output `public/labs/two-button/profiles/macro-entries-v1.json` is checked with `--check`.

| Live BITS profile | Category | Macro entries | Guide selections using them |
| --- | --- | ---: | ---: |
| `bits-literal-joint80-7-v2`, `-8-v1` (and superseded `-7-v1`) | primitive | 0 | 0 |
| `bits-js150-128/256-guide-v1` | macro | 3 / 6 | 9 of 19,979 / 16 of 12,313 |
| `bits-py50-marginal-128/256-guide-v1` | macro | 1 / 1 | 3 of 8,624 / 3 of 4,675 |
| `bits-js150-readable-128/256-v1` | macro | 3 / 6 | 0 / 0 (present, unused) |
| `bits-literal-shared7-v1` (legacy) | macro | 1 (entry 72, 167 bytes) | 8 of 154 |

Legacy shared7 is no longer a default BITS profile: it sits in a picker section labeled
legacy and macro, and its records still replay. In the composition explorer, 10 of 14 sets
(including shared7, compact8, the greedy and span sets, and the whole-program baseline)
are macro sets and are listed in their own table section.

## Promotion

A candidate replaces the live profile of its slot only if all of these hold:

1. It comes from a frozen, committed experiment whose results are committed.
2. Every program in the cohort decodes, through the canonical codec, to a source hash
   with passing recorded qualification; source publication permission covers it.
3. Total selections are at least **2% below** the live profile's on the same cohort
   and sources, and complete package bytes (dictionary plus packets) are no more than
   **5% above** it. A readable candidate must also meet its readable-policy rules.
4. A guide package is built and independently verified (every packet decoded, minimum
   parse lengths checked, hashes and accounting checked), as in
   [guides-qualified-v1](guides-qualified-v1/README.md).
5. BITS focused tests and replay checks pass with the new profile, and difficulty and
   selection counts shown in BITS match the verified package.
6. The report gives the per-problem distribution against the live profile (how many
   programs improve, stay equal or get worse, and the range), not only the total.

A promotion is reported as an improved representation of the same qualified programs. It
is not broader problem coverage, and it is not autonomous solving.

A first profile for an empty slot (for example any 6-bit slot) is promoted only if it
covers its whole declared cohort and beats the cheapest existing profile on that cohort
in total input presses (width plus frame bit, times selections).

## Supersession

When a profile is replaced, it leaves the BITS picker. Its files stay loadable only
where existing attempt records need them for replay, and its Gamma package and receipts
remain in Git history. A larger-cohort profile does not supersede a smaller-cohort one
unless it is also cheaper on the smaller cohort's programs.

## Current bars (80 compact sources)

| Slot | Live profile | Selections | Package bytes |
| --- | --- | ---: | ---: |
| JavaScript 80, literal, 7-bit, primitive | `bits-literal-joint80-7-v2` | 9,910 | 12,798 |
| JavaScript 80, literal, 8-bit, primitive | `bits-literal-joint80-8-v2` | 6,161 | 11,750 |

## Promotion log

| Date | Slot | Replaced | By | Change | Evidence |
| --- | --- | --- | --- | --- | --- |
| 2026-10-21 | JavaScript 80, literal, 7-bit, primitive | `bits-literal-joint80-7-v1` (10,155) | `bits-literal-joint80-7-v2` (9,910) | -2.41% selections, -1.57% bytes; per program 41 fewer, 12 equal, 27 more (median -1, range -42 to +12) | [matched80-v2](matched80-v2/README.md), [guide package](guides-joint80-v2/README.md); 256one `744d3017f`, deployed to one256; live check [receipt](bits-deploy-receipts/2026-10-22-256one-744d301.json) (44 changed public files byte-identical) |
| 2026-10-22 | JavaScript 80, literal, 8-bit, primitive | `bits-literal-joint80-8-v1` (6,413) | `bits-literal-joint80-8-v2` (6,161) | -3.93% selections, -0.26% bytes; per program 55 fewer, 11 equal, 14 more (median -3.5, range -19 to +20); all five frozen seeds 6,161-6,171 | [matched80-v3](matched80-v3/README.md), [guide package](guides-joint80-8-v2/README.md); 256one `f31a4ba`, deployed to one256; live check [receipt](bits-deploy-receipts/2026-10-22-256one-f31a4ba.json) (45 changed public files byte-identical) |

The 2026-10-21 promotion is the same 80 qualified programs represented with fewer
selections; it adds no problem coverage and no solving capability. Deployment evidence is
an independent check: `scripts/verify-live-deploy.mjs <from> <to>` in 256one fetches
every public file changed in the deployed range from https://256.one and compares
SHA-256 with the commit; receipts are kept in [bits-deploy-receipts](bits-deploy-receipts/).

2026-10-22: 256one `6eaee4e` moved shared7 to the legacy section, added the macro report
and fixed the stale BITS browser specs; deployed to one256, 45 changed public files
byte-identical live ([receipt](bits-deploy-receipts/2026-10-22-256one-6eaee4e.json)).
No profile or bar changed.

2026-10-22: 256one `b4230d2` names every vocabulary "problems · style · width · presses"
(+ "macros"), offers five in the picker and hides the 7-bit JS150, readable JS150 and
Python 50 variants (each needs more presses than its 8-bit sibling on the same problems;
they stay loadable and replayable). Input-tree tiles preview literal text. Deployed; 44
changed public files byte-identical live
([receipt](bits-deploy-receipts/2026-10-22-256one-b4230d2.json)). No profile or bar changed.

Not promoted: matched80-v3 7-bit (best 9,784, -1.27%, bar 9,711); matched80-v3 readable
arms (separate scorecard, no live readable 80 slot; the best needs 73,503 presses against
57,717); matched80-v2 8-bit (6,360, -0.83%) and every matched80-v1 arm.

Six-bit ([sixbit-v1](sixbit-v1/RESULTS.md), frozen Mars run, 2026-10-22): no six-bit slot
opens. Exact segmentation proves 64 literal entries cannot cover the 80 compact programs
(certified minima 92 under the witnessed rule and 79 under any-substring entries, which
admit even near-whole-program macros). At most 64 of 80 programs fit in 64 witnessed
entries, at 88,207 presses against 36,621 for live 8-bit on those 64. The separately
specified escape codec needs at least 75,925 presses for primitive dictionaries, against
55,449 for live 8-bit v2; its any-substring result (24,613 presses) depends on macro and
near-whole-program entries and is reported only in the macro category. The Jupiter
compute supplement for the unresolved jobs is still running. Note: the 256one macro
classifier flags only definitions that close inside an entry; near-whole-program entries
that stop before the final brace are not flagged, which matters for any-substring
experiments but not for the live joint80 profiles (entries at most 27 bytes).

JavaScript 150, Python 50 and readable JavaScript 150 slots keep their published
guide-export numbers in [guides-qualified-v1](guides-qualified-v1/README.md); all six of
those profiles are macro category, so a primitive candidate on those cohorts opens a
separate primitive slot rather than competing with them. No 6-bit
slot is live.
