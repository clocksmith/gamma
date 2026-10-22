# Promoting literal results to BITS

Owner direction (2026-10-21): keep iterating on the literal and readable sets, publish
only impressive results to BITS at 6, 7 and 8 bits, and remove superseded profiles
from the BITS picker. This rule decides "impressive" and "superseded" before results
are seen. It does not change [M1-M6](MILESTONES.md) or any frozen experiment gate.

## Slots

A BITS slot is one language, one problem cohort (an exact ID set), one width
(6, 7 or 8 bits of payload plus BITS's frame bit) and one policy (literal
compression, or readable/human-composed). Each slot shows at most one current profile.

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
| JavaScript 80, literal, 7-bit | `bits-literal-joint80-7-v2` | 9,910 | 12,798 |
| JavaScript 80, literal, 8-bit | `bits-literal-joint80-8-v1` | 6,413 | 11,781 |

## Promotion log

| Date | Slot | Replaced | By | Change | Evidence |
| --- | --- | --- | --- | --- | --- |
| 2026-10-21 | JavaScript 80, literal, 7-bit | `bits-literal-joint80-7-v1` (10,155) | `bits-literal-joint80-7-v2` (9,910) | -2.41% selections, -1.57% bytes | [matched80-v2](matched80-v2/README.md), [guide package](guides-joint80-v2/README.md); 256one `744d3017f`, deployed to one256 and verified live |

Not promoted: matched80-v2 8-bit (6,360, -0.83%) and every matched80-v1 arm.

JavaScript 150, Python 50 and readable JavaScript 150 slots keep their published
guide-export numbers in [guides-qualified-v1](guides-qualified-v1/README.md). No 6-bit
slot is live.
