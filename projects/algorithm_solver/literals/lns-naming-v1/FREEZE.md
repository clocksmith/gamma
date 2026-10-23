# Exact dictionary repairs stacked with per-binding naming

Board15, goals2a/2b. Item13's scope_joint256 passes development readiness.
Item11 (recorded e2e2ac605) shows full-fit exact repairs improve R256 fit selections
26108→25258 (3.26%) and validation actions9048→8814 (2.59%). Polish preserves the
repair gain, adding only10fit selections. However, only33validation programs
improve and45worsen, and median actions rise64.5→65.5. It is not ready.

Test whether repairs complement the selected naming representation, separating
source adaptation from dictionary fitting. Predictions and selection rules were
drafted before item11's validation record and remain unchanged. The smaller budget
here (at most12repairs vs item11's54at256) is an explicit limitation; a small or
null stacked gain would not contradict that larger-budget fixed-R result. J2's
1% fit prediction is motivated by its demonstrated headroom; J4's transfer and
J6's breadth/fraction gates are uncertain because gains can concentrate.

## Fixed inputs, arms and source choices

Use only item13's qualified300fit/100consumed-validation IDs and pinned originalR/
scope_joint sources, seed dictionary and qualification inputs. The seed was
selected on consumed validation: this is adaptive development, not confirmation.
Final held-out100/protected66 stay closed. No item15corpus search, timing smoke,
proposal mining or cost tuning preceded this freeze; only synthetic checks and
hashing existing artifacts. No training/model/scorer or new source family.

Four256-entry/eight-bit dictionary arms, starting from scope_joint256:

- seed: fixed dictionary and item13 selected fit sources, no fitting.
- ordinary: two rounds of scope naming and ordinary local dictionary polish.
- lns_fixed: two repair/polish rounds with item13 fit source bytes fixed.
- lns_joint: two rounds of scope naming, exact dictionary repairs and polish.

Ordinary and lns_joint retain originalR, seed and every generated fit variant.
After a dictionary change, exactly reselect the lowest-selection variant for
every problem, tie by source byte length then variant key. Retain all source
variants; dictionaries advance monotonically by the stated objective, with live
receipts for accepted repairs. Naming uses item14's ordinary per-binding search:
resolved capture-conflict graph, single lowercase-letter substitutions/pair
swaps, two sweeps/6000exact trials per call, strict selection improvement. Keep
its pre-score whole-source/body legality guard. No coupled name proposals,
weighted-character objective, compiler compression or additional name family.
These renamings preserve control flow and asymptotic complexity; final execution
qualification remains mandatory. Unsupported lexical/reflection forms stay fixed.

After ALL four fit dictionaries are sealed, every dictionary receives the same
two validation policies:

- fixed_seed: exact item13 scope_joint validation source bytes;
- adaptive: choose originalR/seed by exact cost, then two ordinary naming calls
  under the sealed dictionary, retaining all previous variants at each choice.

No validation refit. These common policies distinguish dictionary changes from
extra source-encoding work. Both views share that dictionary arm's selected fit
sources. All8views×400choices remain in the report, including any failure.

## Bounded exact repairs and shared local polish

For each repair round, construct a pool of2–64byte substrings witnessed by at
least two distinct selected fit owners. Exclude complete sources and solve
function/body strings from ALL retained variants. Rank by overlapping occurrence
count×(length−1), then string. Fix the pool/ranking for that round; after source
reselection it remains a bounded heuristic, not an exhaustive changing-source pool.
Legacy seed entries retain their pinned provenance. Local polish uses its usual
2–6selected-part merges up to160bytes, two-owner support and the same body ban.

Each repair randomly frees up to40learned entries, retaining all96fallback
characters. Offer freed entries, top3000eligible pool strings and up to1000
seeded-random candidates (sample up to3000pool strings then filter). Allow the
full remaining capacity256−len(fixed), including previously unused slots. Use
seed1500+roundindex, shared between LNS arms; differing incumbents/pools still
produce different trajectories. Maximum6calls per round; each has up to120solver
seconds, with a900-second phase guard checked before each call. Pool/model
construction and exact rescoring count toward measured phase time; the final
call may cross the guard. No unreported continuation if a cap is reached.

Reuse item11's HiGHS MILP repair: binary optional dictionary entries, continuous
source-to-sink occurrence flows, capacity constraint. It optimizes only the
CURRENT SELECTED SOURCE SNAPSHOT, not all source variants jointly. Independently
rescore each feasible selected snapshot with canonical literals.py DP. Require
exact<=solver objective+1e-6, and status0 absolute equality within1e-6. Then reselect
all retained variants and record the additional gain separately. Accept only
strict total-fit-selection improvement, legal capacity/fallback and clean body
audit. Solver time-limit incumbents are candidates, not optimality certificates;
status0 is solver-reported optimality of the restricted repair, not a global
or independently certified dictionary optimum.

Persist every move with selected-source hash, pool hash, status/objective/gap/
bound, snapshot/reselected counts, capacity and acceptance; write each accepted
dictionary and source selection before appending its receipt. validation_loaded
is false throughout fitting. All proposal strings and source choices stay private.

After each round every non-seed arm receives the same ordinary polish:
30000exact trials/600seconds, 24refill candidates;96additions,500swaps,150pairs,
16pair-addition/8pair-removal shortlist, designed_fraction0.25 with no supplied
designed entries. Optimize selections then package bytes, retaining the incumbent
when capped. The cap guard skips pruning at an exhausted budget. LNS has extra
compute beyond ordinary; this is a mechanism-plus-budget comparison, not equal
wall time or identical candidate trajectories.

## Seals, qualification and accounting

Pin code/runtime/seed/case hashes and the existing Python3.14.4 SciPy1.18.1/
NumPy2.4.4 environment. Verify exact interpreter path and versions before launch.
All dictionaries and fit sources seal before validation loads. Both validation
views and all choices seal before final source execution. Decode all3200packets
independently to exact selected source bytes. Every distinct changed source/ID
pair passes ALL pinned original cases and strict observation parity in the
existing isolated judge, with four sandbox workers. Unchanged originalR reuses
its pinned receipt. No retries, repairs, test-driven fallback or dropping failures.
Finite reused development tests do not establish universal equivalence.

Whole-source/solve-body audits cover all retained fit and validation variants.
Complete dictionary, eight-bit IDs,41-byte frames, padding and one Finish are
charged. Report selection/action totals and median/p90/p95/worst,<=32/96,
character counts/fractions, paired better/same/worse, qualification failures,
source switches, solver/search budgets/statuses, raw and decoder-source-inclusive
packages and per-program costs. Offline code/parser inventory is separately
reported; pinned Python/solver binaries do not constitute a complete measured
runtime installation. Reporting is separate, rerunnable and may be corrected
without changing frozen choices or rerunning fitting.

## Frozen predictions and selection

- J1: seed/fixed reproduces item13 fit and validation selection counts.
- J2: both LNS arms improve final fit selections by at least1% over seed.
- J3: lns_joint fits below lns_fixed.
- J4: at least one LNS adaptive view saves at least1% validation actions versus
  ordinary adaptive continuation.
- J5: all3200choices decode, qualify and pass whole-solution audits.
- J6: at least one LNS view passes the incremental successor rule below.

Readiness against historical originalR/L-R256 is unchanged: all400choices
qualified,100validation decoded, clean audits, at least5%fewer validation actions,
strictly lower action median/p90, at least60better/at most25worse, nonincreasing
single-character fraction and rawpackage<=105% of control.

Only LNS arms can be selected as the new repair candidate. In addition to full
R readiness, require incremental success against item13 AND against BOTH seed
and ordinary under the SAME validation view: strictly fewer total actions,
no higher median/p90/character fraction, at most25worse, package<=105%, complete
qualification/coverage and clean audits. Rank eligible views by actions, package,
armname, viewname. Report every failed predicate and weaker readiness separately.
Extra naming work cannot qualify as a dictionary-search gain by an unmatched
comparison. M1 indicators are descriptive; the500-problem milestone is unqualified.

## Resources, review and boundaries

Two search processes: cores0–3 run ordinary then lns_joint; cores4–7 run lns_fixed.
Set OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=2; HiGHS is bounded by each process's
four-core affinity (its internal thread count is not separately asserted).
Four common-view encoding workers then four sandbox workers, allcores0–7.
8GiBaddress-space per process and7200-second global hard cap. No GPU/model.
Eight synthetic tests pass, including12 exhaustive tiny MILP comparisons,
sparse-capacity retention, exact source reselection, solver-objective checks,
prune-at-cap, pool support/body exclusions, monotone receipts and naming checks.
Compile/import/help pass. No broad repository or model campaign.

Freeze/code/contract pushed, then Claude review or PLAN30-minute timeout before
launch. Component intent preserved; no canonical codec or production changes.
Confirmation, protected opening, training, BITS deploy, source publication and
human study remain owner-gated. No ledger/catalog/claim writes. Any selected
candidate is a private development artifact awaiting separately frozen,
owner-approved confirmation.
