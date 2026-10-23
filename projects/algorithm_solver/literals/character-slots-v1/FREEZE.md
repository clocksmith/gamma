# Coverage-constrained character-slot selection

Board24, goal2a. Existing256-entry searches fix96single-character entries. Item3
removed seven characters absent from fit and lost three validation programs.
Test a different constraint relaxation: let selected shared literals replace
some fit-OBSERVED character entries, while exact flow constraints retain complete
fit coverage. Reserve ALL fit-unseen fallback characters. This avoids repeating
that particular unseen-character omission, but unseen validation contexts can
still become unencodable. Failures remain failures, without repair or escape.

M1 limits total literal entries, not mandatory alphabet size. This remains the
canonical flat exact-string codec: all source bytes are literal concatenations,
all selections charged, no substitutions or new decoder. It changes a search
constraint, not M1 thresholds or protected-data authority.

## Fixed inputs and matched arms

Use item13 scope_joint256's exact selected300fit/100consumed-validation sources
and dictionary. Only fit sources enter pools, character policy or search. The
seed was selected using development validation; this is adaptive development,
not independent confirmation. Final held-out100/protected66 stay closed. No
corpus cost/character probe preceded this freeze; four synthetic tests and
40exhaustive tiny mixed-character/string cases exercised the new model.

Three arms, all256entries/eight-bit payload:

- seed: pinned dictionary, no fitting;
- fixed96: all96characters fixed, free up to48learned entries per repair;
- optional: free up to8currently selected fit-observed characters, plus enough
  learned entries to free48total (limited by available entries).

Optional chooses up to4characters by lowest current canonical character-use count,
then codepoint; the remainder are sampled from other eligible current characters.
A character absent from ALL fit text is never removed. Previously removed observed
characters remain candidates for reintroduction. This is a fit-only policy.
Report both total character entries and reserved/unreserved counts, without
publishing the actual private codebooks. No source or naming adaptation.

Both searched arms use seed24, the same fixed fit pool/ranking and the same12repair
calls, at most120solver seconds per call and1800-second phase guard. Pool/model
construction and exact rescoring count toward measured phase time; a final call
can cross the phase guard. Offer freed entries plus top3000and up to1000seeded-
random pool words (sample up to3000then filter). Optional additionally offers all
nonfixed fit-observed single characters. Every learned pool word is2–64bytes,
witnessed by at least two distinct fit owners, excluding all complete sources/
solve definitions/bodies. Rank overlapping occurrences×(length−1), then string.
Seeded legacy entries retain pinned provenance. Full capacity is256−len(fixed),
including unused slots. Candidate trajectories may diverge after accepted moves.

No ordinary polish: its mandatory-fallback assumptions would undo the tested
constraint change. Neither arm receives extra search after its cap. This compares
matched bounded procedures, not global dictionary optima or identical wall time.

## Exact coverage model and acceptance

One source-to-sink occurrence-flow DAG per fit program. Include an edge ONLY when
its exact substring is in fixed entries or optional candidates, INCLUDING length1.
There is NO unconditional character arc. Fixed entries need no activation variable;
each candidate has one binary activation shared across all occurrences, with flow
on its edges bounded by that activation. Sum activations<=remaining capacity.
Every edge costs one selection; minimize total flow cost over all300programs.
Continuous path flows plus binary dictionary choices suffice: once the dictionary
is fixed, an integral shortest path exists and is no worse than a feasible flow.
Missing coverage makes the model infeasible, not an implicit fallback channel.

Independently re-encode every feasible dictionary using canonical literals.py DP;
missing coverage fails the run. Require exact total<=solver objective+1e-6, with
absolute equality within1e-6 at status0. Accept only strictly fewer total fit
selections, legal capacity, reserved-character retention and clean body audits.
Order dictionary IDs by retained original alphabet order, then sorted learned
strings. No acceptance by a partial-covered total, byte-only gain or character
fraction. Time-limited feasible results are candidates, not certificates.

Write each accepted dictionary before its live move receipt. Record solver status,
objective/gap/bound, exact cost, capacity, freed character/learned counts, current
character/learned entry counts, pool/source/dictionary hashes and measured time.
Raw strings stay private. A zero or negative solver bound does not create an
independent optimality claim. Retain nonimproving and time-limited attempts.

## Seals, qualification and costs

Both fitted dictionaries seal BEFORE loading validation values. No validation
repair, refit or conditional fallback. Decode every encodable packet and retain
all400IDs. An unencodable program is a regression and blocks readiness; cost
summaries over encodable rows are explicitly partial, and no full-cohort gain is
claimed from them. Final whole-source/body audit includes both splits.

Source qualification is reused by exact hash from item15's independently frozen
seed_fixed_seed receipt, which passes all400sources. Those sources are identical
to item13's selected source files. No new case execution is claimed. Item23's
retained exit137 failure on one unchanged seed source remains historical evidence
of execution sensitivity; item15 started before that outcome and was not its retry.
This stage tests exact reconstruction, not new runtime qualification.

Report both splits: coverage/failure IDs, total/median/p90/p95/worst selections and
actions,<=32/96, character counts/fraction, source bytes, entry counts, paired
better/same/worse, raw and decoder-source-inclusive packages, payload/framing/
padding and per-program costs. One Finish per encoded program, all dictionary
entries and41-byte packet headers charged. Report one-program and amortized costs.
Offline code/parser inventory is separate; complete installed runtime footprint is
unmeasured. Qualification reuse, fit/validation seals and packet hashes are explicit.

## Predictions and decisions

- A1: seed reproduces pinned fit/validation counts, both searched arms retain300fit
  coverage and do not worsen the total fit cost.
- A2: optional's final accepted dictionary has fewer than96character entries.
- A3: optional has fewer fit selections than fixed96.
- A4: optional preserves100/100validation coverage despite changed context coverage.
- A5: optional has fewer validation actions than fixed96, with full coverage in both.
- A6: optional does not pass every incremental successor condition below.

Readiness versus originalR/L-R256 is unchanged:100validation decoded with reused
source qualification, clean audits,>=5%fewer actions, strictly lower action median/
p90,>=60better/<=25worse, nonincreasing character fraction, rawpackage<=105%.
Also require all300fit sources decoded. Candidate promotion is restricted to
optional, and additionally requires incremental success against BOTH seed and
fixed96: strictly fewer validation actions, no higher median/p90/character fraction,
<=25worse, package<=105%, full coverage/qualification and clean audits. Report every
failed predicate, all paired effects and weak readiness separately. No complete-
cohort total comparison is valid with missing coverage. No M1 qualification,
confirmation, human fluency or autonomous-solving claim follows from this run.

## Runtime, checks and boundaries

Two search processes on cores0–3/4–7, after item15 releases those cores. Pinned
Python3.14.4/NumPy2.4.4/SciPy1.18.1 and HiGHS binary; exact interpreter/version
checks. OMP/OPENBLAS2, four-core affinity per solver,8GiBaddress-space per process,
2400-second overall cap,PYTHONHASHSEED0. No GPU/model or sandbox campaign.

Four tests pass: missing characters are not free; a multi-character literal can
cover an omitted character;40tiny mixed-entry problems match exhaustive optima/
infeasibility; reserved-unseen retention and matched48slot freeing. Compile/import/
help and code/runtime hash checks precede launch. Freeze/code/contract pushed,
then Claude review or PLAN30-minute timeout before measurement. Reporting is
separate and rerunnable without fitting again.

Component intent and canonical/production boundaries preserved. No source or
private codebook publication, ledger/catalog/claim writes, training, protected
opening, BITS deployment, human study or M1 change. Any selected candidate still
needs separately frozen owner-approved confirmation.
