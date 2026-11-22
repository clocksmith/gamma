# Results: cheap checks against the flow method on nine unseen projects near 64 characters

Run on 2026-11-22 (UTC). Pre-registration, runner and checker at Gamma `64b1ea0d`; results as run at
`7aa9b02c`; the capped rerun is described in `ADDENDUM-CAPPED.md`. Every lower bound below is a recomputed
rank or a certificate checked in exact fractions. Every dictionary is replayed against the frozen bytes.

**Under the 160-byte entry cap, which is the rule of `sixbit-v1`: eight of the nine projects do not fit 64
entries and one does. The shipped diagnostic certifies all eight rejections, and block rank alone certifies
seven.**

**Correction, same day.** This file first said none of the nine fits. That was wrong: PY-3 was unresolved,
not rejected. The upgraded diagnostic (Gamma `084f50a8`) then found a 62-entry dictionary for PY-3, which
`capped.py` replays as legal. PY-3 has 68 characters and fits 64 entries, so the grid decision does change
on one project of nine. The dictionary is stored in `external-dictionaries.json`.

## A mistake in the setup

The pre-registration said all methods ran under identical entry rules. They did not. The shipped diagnostic
caps a multi-character entry at 160 bytes; the flow method as first run had no cap. I did not check before
freezing. Both runs are reported. The capped one is the like-for-like comparison.

## Capped rule (like for like)

| Corpus | Alphabet | Block rank | Shipped diagnostic bound | Flow certificate | Dictionary replayed | Minimum | Fits 64 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| JS-1 | 69 | 69 | 69 | 69 | 69 | 69 | no |
| JS-2 | 66 | **64** | 65 | 65 | 65 | 65 | no |
| JS-3 | 70 | 70 | 70 | 70 | 70 | 70 | no |
| PY-1 | 69 | 69 | 69 | 69 | 69 | 69 | no |
| PY-2 | 69 | 68 | 68 | 68 | 68 | 68 | no |
| PY-3 | 68 | 51 | 57 | not attempted | 62, from the upgraded diagnostic | 51 to 62 | **yes** |
| C-1 | 69 | 68 | 68 | 68 | 68 | 68 | no |
| C-2 | 67 | 65 | 65 | 65 | 65 | 65 | no |
| C-3 | 70 | 66 | 66 | 66 | 66 | 66 | no |

- **The grid decision changes on one project of nine.** PY-3 has 68 characters and fits in 62 entries. The
  other eight have more than 64 characters and do not fit.
- **Shared fragments save little:** 0, 1, 0, 0, 1, 1, 2 and 4 entries on the eight settled projects.
- **Block rank is exact on seven of eight.** On JS-2 it is one short, and at 64 entries it cannot reject.
  This is the first real corpus where it falls short.
- **The shipped diagnostic's bound equals the minimum on all eight** and rejects all eight at 64 entries. Its
  bound on PY-3 (57) is its own and is not re-checked here; the interval above uses only bounds checked here.
- **PY-3's minimum is still an interval**, 51 to 62, but its answer at 64 entries is settled. The flow
  method did not settle it: 776,363 eligible occurrences under the cap, over the limit set for the linear
  program, and its restricted dictionary search reached only 66.

### Time to the same verified answer

| Corpus | Block rank and forced characters | Shipped diagnostic | Flow method (bound + dictionary) |
| --- | ---: | ---: | ---: |
| JS-1 | 0.04 s | 1.9 s | 10 s |
| JS-2 | 0.02 s | 7.4 s | 161 s |
| JS-3 | 0.03 s | 3.9 s | 33 s |
| PY-1 | 0.05 s | 2.7 s | 30 s |
| PY-2 | 0.03 s | 4.2 s | 42 s |
| PY-3 | 0.01 s | 34 s, no answer at 64 | 258 s, dictionary only |
| C-1 | 0.03 s | 1.0 s | 5 s |
| C-2 | 0.02 s | 2.7 s | 20 s |
| C-3 | 0.05 s | 1.8 s | 16 s |

Single runs on one laptop with other work running, except the first column (best of three). For a rejection
the flow method needs only its linear program, which is about half of each figure in its column.

## Uncapped rule (as pre-registered and first run)

Seven minimums are the same as above. JS-2 differs: with entries of 246 and 175 characters it has a replayed
dictionary of 64 entries and a certificate of 64, so it fits. C-2's dictionary used one entry of 161
characters; its minimum is 65 either way.

| Prediction | Outcome |
| --- | --- |
| B1. Block rank equals every established minimum | held without the cap; **fails on JS-2 with the cap** |
| B2. The flow method establishes at least 7 of the 8 minimums under the size limit | held: 8 of 8 |
| B3. Two to four projects fit 64 entries, JS-2 among them | **wrong**: one fits without the cap, none with it |
| B4. Rejections are certified by block rank alone; fits need a dictionary from the search | held without the cap; with the cap block rank misses JS-2 |
| B5. Cheap checks under 1 second; flow method at least 50 times slower | held on every project |
| B6. The alphabet exceeds the minimum by 1 to 8 | **wrong**: three projects save nothing |

## What this shows and what it does not

- For the question "does this project fit 64 keys", counting characters gave the right answer on eight
  projects and the wrong one on PY-3.
- For rejection, the shipped diagnostic reached the verified answer on all eight in 1 to 7 seconds. The flow
  method reached the same answers in 5 to 161 seconds.
- Neither method benchmarked here gave a "fits" answer when the alphabet is above 64 under the cap. The one
  such case, PY-3, was settled afterwards by a constructor in the upgraded diagnostic.
- Nine projects of four files each, from four repositories of one owner, chosen by a seeded rule written
  by the author of the methods. The flow method is a reimplementation of the published formulation on a
  general solver, not the original authors' software.
- This counts dictionary entries. It says nothing about presses.
