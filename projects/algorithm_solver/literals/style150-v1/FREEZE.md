# style150-v1: frozen design

Owner-approved source-rewriting experiment on the first 150 development problems
([MILESTONES.md](../MILESTONES.md#owner-decision-2026-10-22), goal v2:2b). [contract.json](contract.json)
pins every input by SHA-256 and states every budget, seed, rule and prediction. It was
committed before any rewrite was written and before any arm ran. Results go in a separate commit.

## Hypothesis

The current 150 sources mix equivalent phrasings (`i+=1` and `i++`, `const` and `let`, object
maps and `Map`), so few long strings recur and the best 256-entry dictionary averages about
3 bytes per selection (12,337 selections, 58% single-character). Rewriting every program to
one shared style ([STYLE.md](STYLE.md)) should make whole statements recur across problems,
so a dictionary covers more text per selection.

## Treatment

One rewrite per problem, written by rewriter agents from the original, the best existing
compact variant and the statement, following STYLE.md. Rewriters see no dictionary, encoding
or measurement output. Each rewrite must keep the algorithm and its asymptotic cost, and
must pass every corpus case with the unchanged oracle and strict parity with the original's
recorded observation: result, type, arguments after the call, and alias edges. Rewriters may
run at most 8 parity checks per problem, then submit once. A failing rewrite is recorded and
not replaced.

## Inputs fixed before the treatment

- Cases: the corpus independent cases for all 363 admitted problems, rebuilt uniformly by
  [admission500-v1/population.py](../admission500-v1/population.py); all 363 originals pass
  34,309 of 34,309.
- Existing pool: of the 1,006 scale150 alternatives, 998 pass those cases with strict parity
  ([evidence/pool-requalification.json](evidence/pool-requalification.json)). The 8 failures
  (`legacy-shared` variants of 169 and 961) are excluded from every arm.
- Starting dictionaries D0: scale150-refine token-input 128 and 256.
- Held-out split: sha256(`style150-v1-heldout` + id), lowest 30 held out.

## Arms (each at 128/7 and 256/8)

| Arm | Sources | Dictionary | Isolates |
| --- | --- | --- | --- |
| A | existing pool S1 | D0 fixed | exact-parse control |
| A0 | originals only | D0 fixed | one fixed source per problem |
| B | S1 + rewrites | D0 fixed | source-only effect |
| C | S1 | search from D0 | dictionary-only effect |
| D | S1 + rewrites | search from D0 | joint effect |
| E | rewrites only (original if a rewrite failed) | search from D0 | the style alone |
| CH, DH | as C, D | fitted on the 120 training problems from the fallback alphabet, then fixed | held-out 30 |

Search is matched80-v3's exact local search: deletion harm, 96 hybrid additions (3/4 joint-v1
span order, 1/4 STYLE.md designed forms), 500 swaps and 150 double swaps per round, best exact
move accepted. The same neighborhood and a 100,000-trial cap per search arm (4-hour safety
limit) apply to every search arm. Every packet is decoded independently through the canonical
codec to a qualified source hash.

## Predictions

- P1: at 256 entries, D uses at least 10% fewer selections than C.
- P2: at 256 entries, D's single-character selection fraction is at least 10 points below C's.
- P3: at 256 entries, E uses no more selections than C.
- P4: at 128 entries, D uses fewer selections than C.
- P5: on the held-out 30 at 256 entries, DH uses at least 10% fewer selections than CH.
- P6: at least 120 of the 150 rewrites qualify.

## Disclosure

Before freezing, the runner was smoke-tested end to end with a 300-trial cap and no rewrites,
to check plumbing and timing (about 40 ms per exact trial on Jupiter). Arm A reproduced
scale150-refine exactly (20,155 and 12,337 selections; 25,532 and 22,296 package bytes). Those
smoke outputs are not results and were discarded. Only the trial cap was set after that run.

## Not claimed

M1 is not measured here: 150 is not the frozen 500. Nothing here is autonomous assembly or
unseen solving. A BITS candidate would still need [BITS_PROMOTION.md](../BITS_PROMOTION.md) on
its own cohort slot.
