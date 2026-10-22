# Six-bit capacity on the matched 80

Design: [FREEZE.md](FREEZE.md) (frozen at `2bd349e51` before any job ran) and the
[Jupiter compute supplement](FREEZE-jupiter.md) (declared at `542187a26` before its
targets' results were seen). Codec C: [ESCAPE6.md](ESCAPE6.md). All numbers:
[RESULTS.md](RESULTS.md). Supplement status: [JUPITER_HANDOFF.md](JUPITER_HANDOFF.md)
(running; not yet reported).

## Outcome (2026-10-22, from the frozen Mars run `run-v1`)

All 8 jobs finished on Mars. Every vocabulary, packet and bound was rechecked by
[verify_amended.py](verify_amended.py). The checks decode every packet against the
qualified source hashes, check rules and budgets, and recompute each Lagrangian bound
from the stored potentials over every eligible substring, without trusting the solver.

**A. Exact coverage of all 80 programs with 64 entries is impossible (certified).**

| Sources | Rule W (witnessed) | Rule U (any substring) |
| --- | --- | --- |
| compact | minimum 92 entries (certified, optimal) | minimum 79 entries (certified, optimal) |
| canonical | minimum 92 entries (certified, optimal) | unresolved on Mars: LP hit 1,800 s; best vocabulary 562 entries |

Assumptions behind "impossible":
- Entries are literal strings and a program must be their exact concatenation, as in the
  canonical codec.
- Entries that match no cohort program cannot help.
- W is the live witness rule (multi-character entries in two or more problems, at most
  160 bytes, never a whole program) without the mandatory 96-character fallback.
- U allows any substring except a whole program, so it includes near-whole-program macro
  entries: the U optimum uses 11 of them. The bound of 79 therefore holds for every literal
  vocabulary, macros included.

The minimum is decided by segmentation, not character counts. 92 distinct characters
alone would not prove the bound, since multi-character entries can hold several.

**B. 64 entries cover at most 64 of the 80 programs under either rule (certified).**
- W (primitive): 64 programs in 12,601 selections, which is optimal. That is 88,207
  presses, against 36,621 for the live 8-bit profile on the same 64 programs.
- U (macro category): also 64 programs, in 12,574 selections. Phase 2 hit its limit, so
  this count is not proven optimal.
- Uncovered under W: #4 #7 #9 #67 #387 #551 #657 #682 #709 #748 #824 #844 #892 #917 #929
  #1046.

**C. The escape codec is far behind the live 8-bit profile; not promoted.**
- W (primitive): 75,925 presses, optimal and certified, with 8,485 selections and 1,102
  escapes. This is the minimum for any 63-entry W dictionary under literal-escape6-v1,
  so it cannot reach the bar at freeze (57,717) or the live 8-bit v2 (55,449). It does
  use fewer presses than live 7-bit v2 (79,280).
- U: 24,613 presses, optimal, certified lower bound 24,166. This comes from macro entries:
  22 entries meet the BITS macro rule and 59 of the 63 are near-whole programs. It is
  reported in the macro category and, per [BITS_PROMOTION.md](../BITS_PROMOTION.md), not
  compared with primitive bars.

Predictions:
- P1 (W-strict cannot cover #709, #917, #929) holds analytically.
- P2 holds.
- P3 holds for compact; canonical U is unresolved.
- P4 holds: 64 < 80, and W covers exactly as many as U.
- P5 holds for W. As stated, it fails for U (24,613 < 57,717), but only through macro
  entries, which the macro rule excludes from that comparison.

No six-bit profile is promoted. A primitive six-bit profile would need a smaller declared
cohort or a different codec, and on this evidence would still need far more presses than
the live 8-bit profile.

## Notes

- `verify.py` is pinned by both contracts and stays as frozen. Its one bug compared
  `bitpack.decode` text with bytes, after `literal_codec.verify_packet` had already
  accepted the packet. `verify_amended.py` corrects that comparison and changes nothing
  else.
- Gamma `6035206e1` was an incomplete third-party workspace snapshot of this run in
  progress, not its results; `5b176bb6b` completes `run-v1`.
- The macro measure is a reporting addition, not part of the freeze.
  [classify_macros.mjs](classify_macros.mjs) applies the BITS macro rule (256one
  `macro-entries.js`, read-only) and also counts near-whole-program entries. The BITS
  rule needs a definition whose closing brace is inside the entry, so an entry that stops
  just before a program's final brace is not flagged; the near-whole count catches these.

## Reproduce

```sh
python3 -B -m unittest test_sixbit -v
python3 -B run.py --output run-v1          # Mars limits; refuses an existing output
python3 -B verify_amended.py run-v1
node classify_macros.mjs <256one>/public/labs/two-button run-v1
python3 -B report.py
```
