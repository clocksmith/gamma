# Compact literal search v1: predeclared development comparison

This source-preserving representation experiment uses the exact transferred 300
fit and 100 already-consumed development-validation sources. It neither runs
programs nor establishes fresh qualification, admission or M1. Final 100 and
protected 66 are never opened. All private dictionaries, packets and observations
stay outside the repository. Preserve the original L-R dictionaries and sources.

Before fitting, bind this document, implementation, tests, codec, independent
measurement implementation, transfer policy, source hashes and dictionary hashes
in a new immutable output contract. Verify the exact transfer receipt/allowlist.
Read fit sources only; seal every arm before loading development-validation.

Compare pinned L-R128 and L-R256 with matched selection-control and character-
budget searches, each initialized from its corresponding L-R dictionary. Mandatory
96 printable ASCII/LF entries retain their IDs. New substrings have length 2..64,
occur in at least two distinct fit programs and never equal a full source or solve
body (with or without outer braces). A conservative lexer locates the unique named solve declaration among fully
charged helpers, ignoring strings/comments/expression-position regexes and simple identifier-interpolation templates; complex templates
and ambiguous declarations fail closed. Pool construction uses sorted
64-character suffix prefixes; retain at most 2048 repeated substrings ranked by
occurrence-count times (length minus one), then shorter bytes and lexical order.
This is a proposal heuristic, not a lower bound or global-search guarantee.

Exact segmentation minimizes selection count, breaking ties by the first literal
ID recursively. For each dictionary measure total selections S and character
selections C. Selection control minimizes (S,C); character-budget search minimizes
(max(0,10*C-S),S,C). The character-budget arm cannot exceed its canonicalized initial total selection
count; this prevents reducing excess merely by inflating its denominator. Neither
changes segmentation or M1 thresholds. New dictionaries
keep mandatory IDs and sort learned entries; the pinned baseline is measured in
its original order. Canonicalized initialization is separately recorded.

Each deterministic round considers up to 24 additions by fit-only remaining
character coverage (control uses occurrence saving), and up to 8 least-used
learned entries for removal; evaluate legal additions and one-for-one swaps.
Evaluate every proposed dictionary exactly; unchanged programs reuse exact cached
scores. Accept only a strict objective improvement, ties by dictionary tuple.
At most 8 rounds and 1024 evaluated dictionaries per arm; CPU cap120 seconds per
arm. CPU exhaustion fails the arm, never silently accepts a hardware-dependent
partial search. Evaluation/round cap termination is retained explicitly. No
validation feedback, restarts, training, source rewriting or adapted budgets.

Measure all frozen arms and pinned baselines on fit and then validation using
existing exact scorer, codec verification and an independent bit-level decoder.
Report median, nearest-rank p95, character-bit fraction, full dictionary/packet/
framing/padding/decoder bytes, per-program source hashes and exact round trips.
A successful 400-source decode is representation evidence only, not400/500
correct programs. Preserve every search trace and failure. Report all arms;
validation cannot select a new configuration within this experiment.
