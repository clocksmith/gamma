# Matched literal research protocol

Research protocol, 2026-10-21. Public methods and aggregate evidence only; no paper submission is authorized.
Read with [research map](RESEARCH.md) and [milestones](MILESTONES.md).
This specifies comparisons; an arm is implemented only when its immutable run
receipt names code, data hashes and measured results.

## Literature and adaptation boundary

[ConvexTok, Tempus et al., v1](https://arxiv.org/html/2605.22821v1), sections
3.2–3.3, minimizes token count using occurrence-edge flow and shared token
activation under a vocabulary budget. Its LP relaxation supplies a lower bound;
Det, Bias and Int rounding produce dictionaries followed by shortest-path parsing.
The reported near-optimality concerns its objective and data, not Gamma.
Our restricted adaptation uses a frozen candidate pool, valid UTF-8 string
boundaries, mandatory observed characters, no whole-program entries, and
separate full-package optimization. It is not the original system.
The paper is CC BY 4.0. Its [code repository](https://github.com/JanTempus/tokenisation_lp)
was inspected, but a code license was not verified. No author code is copied or
installed; pin a permitted version/license before any original-system comparison.

[Casel et al.](https://link.springer.com/article/10.1007/s00224-020-10013-w),
section 2.2, measures grammar size by right-hand-side symbol count, optionally
adding rule count. Theorems 2 and 5 establish NP-completeness for one-level
grammars over five symbols under those measures. Their grammar is acyclic.
This supports careful dictionary-cost accounting, not a transferred hardness
theorem for Gamma's multi-program UTF-8 packets or equivalent-source search.

## Frozen comparison unit

Keep JS and Python separate. Freeze problem IDs, exposure, family/interface,
original and independently qualified alternative source hashes, oracle and
mutation/alias/type/numeric/exception observations, complexity obligations,
candidate strings, whole-body exclusions and support by distinct problems.
Hash inputs before running. Do not mine protected 66 or any reserved heldback.
The current 150 JS and initial 25 Python programs are exposed development data;
neither is a frozen 500-problem M1 qualification population.

For each language, define S0 (one fixed control source per problem), S1 (same
problems plus qualified alternatives), and D0 (frozen control dictionary).
All methods within a comparison receive the identical frozen candidate pool;
candidate mining is a separately charged factor, not hidden extra information.
For source ablation, pool candidates across S1 once and give that same pool even
to fixed-source methods. Report distinct-problem support, not variant inflation.

| Arm | Source choices | Dictionary choices | Purpose |
|---|---|---|---|
| A | S0 | D0 | Exact parsing control |
| B | S1 | D0 | Source-only effect |
| C | S0 | Same frozen candidates | Dictionary-only effect |
| D | S1 | Same frozen candidates | Joint effect |

Within C/D compare Gamma exact-marginal local search with an independently
implemented restricted occurrence-flow LP, Det/Bias/Int rounding and exact DP.
Use bounded integer optimization where feasible. A small BPE implementation
may be an additional clearly labeled restricted baseline, not a substitute for
the stronger flow baseline. Whole-program memorization remains diagnostic only.

## Objectives and bounds

Run 128-entry/7-bit and 256-entry/8-bit arms with the same corpus and source pool.
Primary objectives are reported separately, with the Pareto alternatives retained:

1. Selection count N; payload b*N bits at fixed width b.
2. Actual package bytes: 8 + sum(4 + UTF8_bytes(entry)) +
   sum_programs(41 + ceil(b*N_program/8)).

Decoder/runtime/model storage, controls, navigation, selector bits and offline
source/candidate search time are additional explicit columns, not zero-cost
assumptions. No cluster selector exists in a single shared dictionary. Source
variant choice is offline: the chosen packet itself fully specifies the result.
Seven-bit wins payload unless eight-bit uses less than 7/8 as many selections.

For each literal t use activation y_t; for each source-offset occurrence edge
use flow x_e. Unit source-to-end flow reconstructs the source, x_e <= y_t,
sum(y_t) <= cap. Mandatory characters consume cap and bytes. In a finite-source
extension, choose exactly one variant z per problem and gate its flow by z.
Integer packet-size variables q_p with b*sum(x_e for p) <= 8*q_p charge padding.
Minimize either sum(x_e) or dictionary activation bytes plus sum(q_p).
Relax integer variables to [0,1] (q nonnegative continuous) for the LP bound.
This is our cost extension, not ConvexTok's published objective.

Report feasible incumbent U, solver bound L, U-L and (U-L)/U, time limit,
termination, residuals and integrality tolerance. These concern only the frozen
candidate/source pool. LP values are numerical bounds subject to solver
tolerances, not formal rational certificates. No bound proves global optimality
over all equivalent JS/Python, unmined strings or alternative representations.
Never compare a selection lower bound with a package incumbent as one gap.

## First bounded experiment and acceptance

Start with the already qualified JS tree problems 104/110/111/124, original
complete sources: a small four-program fixed-source solver diagnostic. Mine
length 2–32 character substrings shared by at least two distinct problems;
retain top 320 by support*(length-1), deterministic lexical tie-break, plus
all observed characters. Exclude complete sources and complete solve bodies.
Freeze exact pool/source hashes before solving. This deliberately restricted
pool makes a valid local bound, not a 150-program or M1 result.

At each width and objective use at most 20 seconds LP, 30 seconds MIP, and
30 seconds exact-marginal greedy search, one CPU thread. Retain all rounded
arms, including underfilled dictionaries. Maximum four width/objective cells,
320 seconds solver/search time, 1 GiB RAM, 256 MiB artifacts. No installations.
Existing SciPy 1.15.2/HiGHS runtime is available. Do not overlap resource limits
of the two language workers. If a solver times out, preserve its incumbent/bound.

Independently reconstruct every packet, verify every source hash and objective,
and compare fixed-dictionary DP against flow paths. Small enumerable fixtures
must test integer optimum and LP ordering before corpus execution. Source bytes
are unchanged, so reuse pinned native qualification; any rewrite requires fresh
execution. Preserve failed arms and unsupported inputs. Then extend the same
method to the frozen Python baseline and JS finite variants only after this
diagnostic passes, with a new contract and fair compute budget.

Report coverage, total/median/p95/worst selections, character-bit fraction,
dictionary/payload/padding/framing/package bytes, reuse, whole-solution count,
decode/native correctness, time/memory and shared-subset regressions. Success is
a reproducible stronger baseline or measured gap, not an assumed Gamma win.
No autonomous solving or generalization claim follows from offline encoding.

## Diagnostic status

The first four-source diagnostic is completed; [results and limitations](research-loop-v1/RESULTS.md) and [numeric receipts](research-loop-v1/evidence/flow-aggregate.json) distinguish it from the broader planned joint-source comparator. No matched superiority over the original ConvexTok implementation is established.
