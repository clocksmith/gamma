# neartie-audit-v1: neither fraction-only near-miss is a tie-break artifact

## Provenance

- **Design:** [FREEZE.md](FREEZE.md) (`d61661eee`), plus [amendment 1](AMENDMENT-1.md)
  (`60207332a`), which adds full readiness to item 14's successor rule.
- **Review:** Codex reviewed both and approved before launch (gamma-team LOG 19:43Z and 19:44Z).
- **Run:** one process, under a second.
- **Evidence:** [evidence/results.json](evidence/results.json) holds per-arm summaries and the
  predicate checks of every comparison under every pairing. It has no source text, dictionaries or
  sequences.

## Result (dev-val 100; fixed sources and dictionaries; qualification reused from the recorded receipts)

| Comparison (frozen rule) | historical (both canonical) | matched (both shortest_min_char) | mixed (candidate tie-break only) |
| --- | --- | --- | --- |
| item 10 joint128 vs searched control128 (input candidate) | fails: fraction 81.95% vs 78.67% | **fails: 81.95% vs 78.67%, unchanged** | fails |
| item 14 coupled_joint vs seed (successor, including readiness vs control) | fails: 49.91% vs 49.89% | **fails: 49.16% vs 49.13%** | passes: 49.16% vs 49.89% |
| item 14 coupled vs seed (successor) | fails | **fails** (identical rows) | passes |
| item 14 coupled_joint vs control256 (input candidate) | passes | passes | passes |

**Correctness checks.** All 1,200 packets decode through the canonical flat decoder. Canonical
reproduces every recorded per-problem selection count and single-character count, and the historical
pairing reproduces exactly the recorded failing predicates (asserted). Selections, actions and package
bytes are identical across the two policies. Only the single-character counts move.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| Q1 | canonical reproduces all counts and the historical failures; all packets decode | **Met** |
| Q2 | matched: item 10 joint128 still fails the fraction predicate | **Met.** No tie headroom at all in either 128-entry arm |
| Q3 | matched: item 14 coupled_joint passes the successor rule | **Not met.** The seed gains the same tie headroom (49.89% to 49.13%), so the 0.02–0.03 point gap survives |
| Q4 | mixed: item 10 fails; item 14 passes | **Met** |
| Q5 | coupled_joint vs control256 passes under all pairings | **Met** |

## What it means

- **Neither near-miss flips under a matched encoder**, so neither verdict is an artifact of the
  canonical tie-break.
  - Item 10's 128-entry fraction rise is real: total selections fell faster than single-character
    codes, and there are no ties to exploit.
  - Item 14's successor gap persists because the seed benefits equally.
- **The mixed pairing would flip item 14, but it is not a fair comparison.** It gives only the
  candidate the better encoder. A real encoder change would apply to every arm, and the matched
  pairing shows that it does not change the outcome.
- **No recorded verdict, packet or readiness selection changes.** Item 13's scope_joint256 remains
  the ready input candidate, and confirmation remains the owner's gate. Nothing here touches M1.
