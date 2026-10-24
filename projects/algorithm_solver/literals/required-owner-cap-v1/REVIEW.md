# Item 61 proof-only review

Component: `projects/algorithm_solver/literals/required-owner-cap-v1`.
Gamma goal and CATSCAN constraints are preserved; no boundary changes or
prior-record edits. This record contains a theorem, explicit supplied-input
oracle and invented tests only. It authorizes no private access or execution.

Root and independent composition review found no mathematical blocker. The
wording uses the "defined range k>=r", not "nonempty range": the coverage floor
is necessary and is not a feasibility certificate.

Every shared-only-uncoverable source must own at least one selected one-owner
entry. Distinct forced owners require distinct entries. Initializing each such
owner at f_p(1), then selecting largest remaining nonincreasing marginals, gives
the exact finite constrained numerical allocation. Nonnegative increments make
sum t=j and sum t<=j equivalent within available cardinality. Tied/zero values
retain real finite entries and deterministic prefix order. No fake slots or
fixed mandatory vocabulary entries are introduced.

The same actual-path penalty inequality and unchanged full-DAG minimum give
weak duality. The constrained domain is a subset of item 57's, proving dominance
for k>=r. Below r, outputs mark the class empty and leave charge/numerator/bound
null. The bound targets penalties used on paths, not dictionary activation sums.
Free skips belong only to the inherited scheduling upper bound.

The strict example is at a proved feasible minimum support budget: B=3, k=2,
source strings abba/cc/aa, global whole-source bans, character-only original q=0,
and q53 from the resulting distances. Dictionary {a,b,c} covers all sources;
only b and c have one owner. Required-owner charge28 improves on charge38 with
identical L72. The gain disappears by k3. Exhaustive checks also retain a case
where k=r does not cover, and a banned-shared-singleton case forcing sources
without private characters. The accepted56 private-character equivalence is
therefore not generalized accidentally.

Six focused tests passed in 0.122 seconds. They include 24 deterministic tiny
random instances, independent interval subsets and integer allocations, every
covering dictionary and complete path, capacities0/1/2/excess, all budgets below
r, shared/one-owner singleton accounting, repeated ownership, stable zero ties,
negative/bool/missing-validity rejection and optimized-Python refusal.
The tests import item57's explicit oracle as the baseline; they do not import
its production kernel or use private artifacts. This shared baseline boundary
is intentional and is not a claim of wholly independent full-pool computation.

No corpus effect, performance estimate, source correctness, feasible corpus
witness, multiplier optimum, M1 admission, novelty or promotion is established.
The next step requires an explicitly approved implementation design; none is
included in this proof record.
