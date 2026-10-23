Historical design draft, superseded by [FREEZE.md](FREEZE.md) after item11 recorded.

# Draft: exact dictionary repairs stacked with per-binding naming

Board15. Not frozen and not launch authority. Item13 is recorded; item11 is still
running. Implementation preparation can proceed on its reviewed repair method;
final freeze/launch waits for the item11 record. No unsealed validation is consumed
in this draft. No corpus search, smoke or tuning is authorized by this document.

## Question and fixed development inputs

Item13's scope_joint256 is the selected ready development candidate. Item11 tests
exact dictionary repairs on original R. Stack those mechanisms on the fixed item13
seed and isolate source adaptation from dictionary fitting. Keep its fit300/
validation100 allowance, source/qualification identities and M1 gates. Consumed
validation and seed selection are adaptive development, not confirmation.

Tentative256-entry arms:

- seed: item13 fixed dictionary and selected fit sources, no fitting.
- ordinary: two rounds of scope-local naming plus the shared local dictionary
  search, retaining original R, seed and prior variants.
- lns_fixed: two exact-repair/local-polish rounds with item13 fit sources fixed.
- lns_joint: two rounds of scope-local naming, exact repairs and local polish,
  retaining original R, seed and prior variants.

Naming uses two sweeps/6000exact trials per call, single-letter substitutions and
pair swaps, item13 capture constraints. Use item14's pre-score whole-body legality
guard but no coupled proposals. No weighted objective, compiler compression or
new name family. This intentionally starts from the selected item13 mechanism.

Each dictionary gets two validation views, identical policies across arms:
fixed_seed uses item13's exact validation source bytes; adaptive chooses original
R/seed by cost then runs two naming calls under the sealed dictionary. No refit.
Thus common fixed-source and common adaptive-encoder contrasts separate dictionary
and encoding effects. Final fit sources are common to the two views of an arm.

## Exact repair boundary

A repair is exact only for its current selected-source snapshot and candidate
set, with the kept entries fixed. It is not an exact joint source-variant solve.
After a dictionary change, reselect among retained fit variants and record that
additional effect separately. A new dictionary can never discard a better source
variant silently. lns_fixed has only seed fit variants; its source is truly fixed.

At each round, build the shared2–64byte candidate pool from selected fit texts;
exclude all complete source/solve-body strings from every retained variant. Keep
that pool/ranking for the round. Every repair frees up to40learned entries, keeps
all96fallback characters, and offers freed entries plus top3000and1000seeded-random
eligible pool strings. Budget =256-len(fixed), preserving sparse free capacity.
Candidate references require two fit owners; seeded legacy entries retain their
pinned provenance. Source reselection within the round can change the selected
texts while the proposal pool remains fixed, a disclosed bounded heuristic.

Tentative budget refinement: at most6repair calls per round, each at most120solver
seconds, plus a900-second phase guard checked before each call. Model construction
and exact rescoring are charged in wall time and may extend a final call beyond
that phase guard; an independent hard overall cap bounds the run. These counts,
solver limits, seeds and hard cap must be finalized in FREEZE/code/contract before
launch. They replace the earlier informal LOG sketch of purely900-second loops.

Check every feasible solver result: independently rescore the selected snapshot,
exact<=solver objective+1e-6; status0 requires equality within1e-6. Accept only a
strict whole-fit canonical selection improvement after source reselection, clean
body audit and legal capacity. Record solver status/gap/bound/objective, selected-
source hash, exact before/after costs and retained variant choices. A timeout's
feasible point is a candidate, not a certificate. Never call status0 an independently
certified optimum. Persist each move and every accepted dictionary/source selection
as it finishes, with validation_loaded=false.

Use the same local refill/swap/pair polish after each round for all non-seed arms,
with30000trials/600seconds and exact cap-retaining pruning. Every accepted source
and dictionary choice remains available. Full-source minimumN is the objective;
no changed M1/fraction scoring or retrospective preference for an observed winner.

## Qualification and decisions to finalize

Seal all final dictionaries, fit variants and validation choices before source
execution. Independently decode all packets; final changed source/ID pairs pass
all pinned cases with strict observation parity, no retries, repairs or test-driven
fallback. Unchanged original R reuses its receipt. Preserve failures in denominators.
Report all8arm/view pairs, source choices, search status/budgets, raw/decoder-inclusive
costs, characters, quantiles, paired effects and each failed predicate.

Keep existing input readiness versus R/L-R256. Separately evaluate an incremental
successor versus item13: fewer actions, median/p90/fraction no worse, package<=105%,
<=25worse, qualification/audits clean and original-control readiness. Compare the
adaptive views to the seed adaptive view as well as historical item13, so extra
naming work cannot masquerade as dictionary improvement. Rank/predictions remain
to be frozen after item11 records; do not run first and decide later.

Suggested resources: two search processes on disjoint four-core sets, at most two
BLAS/solver threads each, then four sandbox workers. Pin the existing SciPy runtime
from item11, code dependencies and numerical libraries; no GPU/model downloads.
Source rewriting remains offline, not autonomous assembly. All owner gates remain.

## Draft decisions set before item11 validation is recorded (20:27Z)

Predictions, to be carried unchanged into the final freeze unless a dated reason
is recorded before any item15 measurement:
J1 seed/fixed reproduces item13 fit and validation counts;
J2 both LNS arms improve final fit selections by at least1% over the seed;
J3 lns_joint fits below lns_fixed;
J4 at least one LNS adaptive view saves at least1% validation actions versus the
ordinary adaptive continuation;
J5 all3200choices decode, qualify and have clean whole-solution audits;
J6 at least one LNS view passes the incremental successor rule below.

Only LNS arms can be selected as the new repair candidate. For either view require
full existing readiness vs originalR, plus the item13 incremental rule, plus that
same incremental rule vs BOTH seed and ordinary under the SAME validation view.
The incremental rule is strictly fewer total actions, no higher median/p90 or
character fraction, at most25worse, package<=105%, all100qualified and audits clean.
Rank qualifying views by validationactions, packagebytes, armname, viewname.
Report all comparisons, including weaker readiness without successor status.
This intentionally prevents extra naming calls or ordinary continuation being
credited to the MILP mechanism. M1 numeric gates remain unchanged.

Final proposed resources: two search processes; cores0–3 handle ordinary then
lns_joint sequentially, cores4–7 handle lns_fixed. Two solver/BLAS threads per
process;8GiBaddress-space each;7200-second overall hard cap. Four common-view
encoding workers then four sandbox workers, allcores0–7. Exactly two rounds,
at most6repair calls/900phase seconds with120solver seconds per call, seed1500
plus roundindex shared across LNS arms. Localpolish30000trials/600seconds. No
extra run if a cap is reached. A final solver call/model construction can cross
the phase guard; report measured time, retain each accepted live receipt.
