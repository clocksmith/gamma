# Supplying the known feasible incumbent to exact repairs

Board26, conventional search implementation diagnostic. Item15 and live item24
have retained time-limited solver calls whose feasible result is worse than the
known incumbent. All freed incumbent entries remain candidates, so a feasible
incumbent dictionary AND complete path flow already exist. SciPy's milp wrapper
does not supply that point. Test whether giving the exact point to the same
pinned HiGHS solver helps within a matched budget. No objective or gate change.

## Fixed fit-only pairs

Use item13 scope_joint256 seed dictionary and300fit sources. No validation source
values or cases, held-out100 or protected66. Source qualification reuses item15's
seed_fixed_seed receipt by exact fit hash. Item23's retained execution failure is
not retried or revised. No corpus preparation/search probe preceded this freeze;
only synthetic models and installed SciPy/HiGHS API/source inspection.

Build item24's full fit-only pool/ranking once: shared2–64byte substrings,
whole-source/solve-body exclusion, overlapping occurrence×(length−1) ranking.
Prepare EIGHT independent repair snapshots from the SAME unchanged seed, before
any solver call, with seeds260..267. Trials0–3keep all96characters fixed and free
48learned entries. Trials4–7use optional observed characters: free up to8characters
(up to4lowest seed canonical usage, remainder random) plus learned entries to48.
All fit-unseen characters remain fixed. Offer freed entries, observed missing
characters for optional, top3000 and up to1000filtered seeded random pool entries.
Full capacity256−len(fixed). No sequential acceptance, adaptive selection,
validation tuning, source rewrite or polish. Model inputs/hashes seal before calls.

For EACH snapshot, construct one exact item24-style occurrence-flow model. Actual
selected strings only, including optional length1arcs; shared candidate activation,
flow<=activation, budget and per-source unit flow, every edge cost1. Both conditions
use precisely the same matrix/objective/bounds/integrality/candidate order.

- cold: pass the model to a fresh HiGHS object, then run;
- warm: pass the same model, set its fully specified incumbent solution, then run.

Incumbent binary variables select all incumbent candidates; canonical seed paths
supply0/1occurrence flows. Before either condition, verify column bounds,
activation integrality, EVERY row bound and exact objective identity using the
actual sparse matrix. Missing coverage/unknown incumbent entries fail closed.
setSolution must return kOk. After a warm solve, the solver must retain a feasible
objective no worse than the supplied incumbent; failure is an explicit run error,
never hidden by returning the incumbent ourselves.

## Solver and matched execution

Use the existing pinned SciPy1.18.1 bundled `_highspy._core` binding, Python3.14.4,
NumPy2.4.4, exact HiGHS binary hash. This version-specific internal binding is
research-local; no installed package or production API changes. Both arms use
fresh objects and identical output_flag=false,time_limit90seconds,mip_rel_gap0,
threads1,random_seed260; other options remain identical defaults. No objective
cutoff, extra constraints or heuristic changes. MIP-start setup is the only
condition difference. Solver-run budget is equal; complete API-call and shared
model-build time are separately charged, including start setup overhead.

Run the two conditions sequentially on the same core per snapshot. Even-numbered
trials cold-first, odd warm-first; order is balanced within each repair type.
Four pair workers on cores12–15, trial modulo4. Eight pairs/16solver calls total;
8GiBaddress-space per process,1200-second overall cap,OMP/BLAS1/PYTHONHASHSEED0.
Our item24 has2workers and25has4, so all three total10search workers, below12.
Claude22's cores26–31 stay separate. Check host load/board before launch.

After each call, persist solver status/feasibility/objective/bound/gap/node count,
run/call timing and model hash before decode. Independently verify the returned
full solution satisfies all bounds/rows/integrality within1e-6. Select its binary
entries and rescore canonical paths. Exact cost<=solver flow objective+1e-6;
status-optimal requires equality. Time-limited flows may be nonminimal for their
chosen dictionaries. Decode ALL300fit programs for each feasible result. A cold
infeasible/no-result call stays failed in its denominator; do not invent costs.
No retry, objective repair or fallback candidate. Capacity and fit body audits
remain mandatory. Private snapshots, vectors, dictionaries, sources and packets
are not published; metadata includes hashes and per-program costs only.

## Reporting and predictions

Report pairwise warm/cold exact costs, solver objectives/status/gaps, improvement
versus the seed, feasible/nonworse/improving/optimal counts, node counts, per-call
and total time, separately by fixed96/optional and overall. Pairs with no cold
feasible point have an unavailable numeric delta and a separately counted warm
feasibility advantage. Aggregate costs over incomplete cohorts are explicitly
partial. Do not sum independent dictionaries into a fictitious shared vocabulary.
All entries/selection actions/Finish/41-byte packet frames/storage are charged
per result; distributions, character fraction and one-program/amortized packages
are retained. Source execution is reused, not rerun. Decoder source inventory is
separate; full installed runtime footprint remains unmeasured.

- W1: every warm solve is feasible and its exact cost is no worse than the seed.
- W2: warm strictly beats cold exact cost in at least4of8pairs with both feasible.
- W3: warm finds a strict seed improvement in at least6of8snapshots.
- W4: warm reports optimality in more snapshots than cold.
- W5: all feasible final dictionaries decode300fit programs and pass capacity/body
  audits; every algebraic start check passes.
- W6: warm's summed complete call time is no more than105%of cold's.

No readiness or candidate promotion. Warm starting becomes a proposed tool for a
future frozen search if W1/W5hold and it yields at least one strict paired cost
improvement or feasibility advantage without any paired exact-cost regression.
Otherwise retain it as an inconclusive/negative matched diagnostic. Even a tool
recommendation does not authorize rerunning any frozen prior experiment or claim
validation/generalization/M1 gains. Report every contrary pair and order.

Four synthetic tests pass, including32tiny dictionary problems compared against
exhaustive enumeration AND SciPy's old solve for both cold/warm direct calls;
optional-character coverage; invalid starts; and preserving a supplied feasible
point with zero solver time. Compile/import/help and exact code/runtime/input
hash verification precede launch. Freeze/code/contract pushed, Claude review (or
PLAN30-minute timeout) before any corpus preparation or solver call. Reporting
remains rerunnable without solving again.

Component intent preserved; canonical literal codec and production boundaries
unchanged. No training, source publication, protected opening, ledger/catalog/
claim writes, independent confirmation, deployment or human study.
