# Joint composable exact-literal comparison, version 1

Owner: [Algorithm Solver charter](../../CATSCAN.md). This is a new experiment,
not a change to historical contracts, sources, results or M1 thresholds.

## Hypothesis and scope

Short and medium recurring fragments, plus complementary two-fragment moves,
can expose source/dictionary improvements missed by long raw-saving proposals.
Sources are exact strings, not macros, bindings, generated code or free adapters.

The control population is the frozen permitted 400 development problems. The
original implementation remains available whenever its new runtime replay passes.
An original failing the unchanged runtime budget remains a retained failure; a
fully qualified adapted successor can supply that problem's reference source.
Such a 397-original/3-successor reference is explicitly not an all-original arm.
Every optional alternative must pass complete source-bound adapted qualification.
No problem is dropped. Final held-out 100 and protected 66 remain closed; the M1
population denominator stays 500 and this experiment does not itself declare M1.

## Source and evidence gate

Independently replay the full baseline receipt, including failures, and each
adapted receipt. Summary pass flags alone are insufficient. Freeze every input,
source, charged adapter, qualification and code identity. The pool must cover all
400 before search begins. Alternatives are allowed only for the 300 dev-fit IDs.
The 100 development-validation IDs retain their reference source choice.

Fit only on the 300 development-fit sources. Seal all four dictionaries and all
source choices before loading validation source contents for measurement. Runtime
qualification verification may hash/replay previously consumed validation inputs;
those inputs never enter proposal or selection code.

## Frozen search

- Four arms: 128/256 entries crossed with selection/character-budget objectives.
- The same 96 paid ASCII+LF characters; no free fallback channel.
- Pool: exact substrings of length 2..64, witnessed in at least two distinct fit
  problems across alternatives. Retain at most 1,500 entries, at most 300 per
  length bucket: 2–4, 5–8, 9–16, 17–32, 33–64. Fit-only occurrence saving ranks
  entries inside each bucket. Reject complete sources, solve definitions/bodies,
  and complete Solution method definitions/bodies.
- Start from the pinned L-R dictionaries. A banned initial entry fails closed.
  Learned entries use fixed lexicographic ordering for canonical decode ties,
  including the initial dictionaries in all matched control profiles; the original
  pinned dictionary bytes and their hashes remain unchanged.
- For each dictionary choose each problem's source by (minimum selections,
  minimum character selections, reference-first stable source identity).
- Selection objective: total selections, then character selections. Character
  objective: max(0,10*characters-selections), then selections, then characters;
  total selections may not exceed that arm's initial reference selection total.
- At most 4 rounds, 512 exact evaluations and 300 CPU seconds per arm. This resource budget is set before any fit (566 source variants), not adjusted
  from observed results. CPU expiry
  is an arm failure, not a partial machine-dependent accepted result.
- Each round balances up to 4 additions from each length bucket. Consider single
  additions/removals and complementary pairs. Pair ranking counts adjacent
  occurrence joins plus the individual heuristic. At most 8 weak removals for
  singles, 4 for pairs, and 12 pair proposals. Every accepted move is verified
  against the independent canonical exact encoder for every source alternative.
- Existing Graph occurrence/affected-program caches only avoid redundant exact
  work; they do not approximate scores, assume submodularity or authorize pruning.

## Measurement and stopping

Seal dictionaries and chosen source hashes before any validation measurement.
At each width/objective, report reference/initial-dictionary, chosen-source/
initial-dictionary, reference/final-dictionary and joint/final-dictionary costs.
Report fit, validation and all400 medians/p95, character bits, all helpers and
adapters, dictionary/packet framing, padding and decoder bytes. Independently
reconstruct every measured packet to the exact selected source bytes.

Keep all failures, excluded alternatives and source choices. No training,
protected scoring, model download, deployment, uncharged helper or automatic
publication is authorized by this comparison.
