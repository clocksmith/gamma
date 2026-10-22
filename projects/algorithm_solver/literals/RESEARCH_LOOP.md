# Research feedback loop and discovery gate

Research protocol, 2026-10-21. This records the owner's research direction. It does not schedule fleet work, authorize protected-data access, or change the literal decoder. Read the [matched baseline protocol](BASELINE_PROTOCOL.md), [research mapping](RESEARCH.md) and unchanged M1–M5 thresholds in [MILESTONES.md](MILESTONES.md).

Dynamic programming, graph rewriting/reduction, self-referential compression and ring all-reduce are hypotheses to distinguish experimentally, not evidence that a particular method must win.

## Iterate between frozen experiments

Problem sets, correct source alternatives and literal vocabularies may evolve together between experiments. Within an experiment, freeze them and their budgets before observing outcomes. A failed comparison is a useful decision point; preserve it before changing the next proposal.

1. Inspect the latest per-problem costs, failed coverage, candidate-support distribution, runtime profile and correctness failures. Select one falsifiable bottleneck, rather than broadening the corpus and changing several methods without attribution.
2. Freeze the admitted development population, exposure labels, original/alternative hashes, oracle/mutation/alias/type/numeric/exception checks, complexity requirements, dictionary candidate pool, controls, budgets and success criteria. Retain failures in denominators. Keep heldback/protected data out of proposal generation.
3. Run exact fixed-dictionary parsing and the source-only, dictionary-only and joint arms in [BASELINE_PROTOCOL.md](BASELINE_PROTOCOL.md), separately for JavaScript and Python and at 128/7 versus 256/8. Changes in candidate mining, compute or source availability are explicit factors. Validate every new source before it can compete.
4. Independently decode and re-minimize packets; compare full package and input costs, quantiles, fallback, reuse and shared-subset regressions. Test the causal explanation with an ablation or counterexample. Record both a solver bound's restricted scope and any heuristic shortlisting limitation.
5. Retain non-dominated candidates and failed approaches. Use the result to choose the next controlled rewrite, dictionary move, representation proposal or admitted-population increment. Link immutable predecessor/successor receipts; never relabel exposed data as unseen. Re-freeze before the next measurement.

This loop can continue while milestones remain unmet; it does not weaken their gates. Expansion and optimization are both available decisions. A 363-eligible inventory is a coverage dependency, not a reason to stop optimizing existing qualified sources. Any larger admission or frozen 500 population definition remains an explicit ownership/contract decision, not a silent training expansion.

## Hypotheses and representation boundaries

| Hypothesis | Concrete first test | Boundary and rejection condition |
|---|---|---|
| Dynamic programming over qualified source alternatives and occurrence paths | A graph node identifies a verified source alternative and offset; exact matching-string edges encode that alternative. Couple path choice to dictionary activation in a restricted finite pool, compare with existing exact per-source DP and joint local search. | Fixed-dictionary DP already exists. The proposed gain must come from source/dictionary choice or candidate generation. Reject a claimed new contribution that only reproduces shortest-path parsing. Any bound covers only the frozen pool. |
| Source-graph reduction and rewriting | Propose semantically justified alternatives or deduplicate equivalent structural states; retain exact source-byte witnesses, qualified interfaces and counterexamples. Compare matched source-only/dictionary-only/joint arms. | Search metadata cannot emit hidden source. Removing states must preserve required solutions or disclose approximation. A finite verified-source graph is the prioritized test; no general equivalence engine is implemented. Related work includes babble's equivalent-program/library search and ConvexTok's occurrence-flow formulation. |
| Recursive or self-referential dictionary compression | Separate experimental format with explicit expansion semantics, termination conditions, expansion/depth limits and full stored rule/edge/decoder costs. Compare decoded identical sources and complete storage against flat literals. | Recursive/cyclic dictionary expansion changes the representation. It cannot inherit seven/eight-bit flat-literal accounting. If entries are flattened, charge every resulting UTF-8 byte. Runtime recursion inside fully stored JavaScript/Python source remains ordinary counted code, as in the qualified tree-fold experiment. |
| Ring all-reduce | Only if profiling shows enough independent scoring work and aggregate communication benefit: compare coordination overhead and elapsed search at matched total compute. | Ring all-reduce is distributed aggregation/coordination, not an intrinsic compression method. It provides no vocabulary-quality claim by itself. This is a proposal only; no fleet jobs, connections, services or distributed experiments are launched by these documents. |

## Energy-guided candidate evaluation (goals v2:2a/2b and v2:4c)

Status, 2026-10-21: a local candidate interface, exact-cost baseline and synthetic
mechanism checks are implemented. No learned energy model has been trained or
shown to improve solving. The previous proposal below remains the rationale;
implementation does not inherit its hoped-for outcomes. Canonical goal IDs,
M1–M6 gates, qualification authority and protected boundaries are unchanged.

The private implementation and immutable receipts are in
`/home/x/Documents/Codex/2026-10-19/task/gamma-energy-candidate-harness-v1`.
Its `PROTOCOL.md` supplies the frozen experiment procedure, `smoke-001` records
24 mechanism tests, 18 synthetic seed/policy/width comparisons and a 32-state
exhaustive reference. These test the harness, not real problem solving or an EBM.
The existing [goals](../../../GOALS.md) and [algorithm component charter](../CATSCAN.md)
remain authoritative; this section is part of the existing research loop, not a
new competing goal register.

### Two evidence tracks

- **Track A: vocabulary and qualified source-choice optimization.** Repeatedly
  diagnose costs and failures on exposed development data, design or mine exact
  pieces, qualify alternative algorithms, then freeze and compare a finite
  source/library search. Maintain separate compression-first and readable-piece
  policies at 64/128/256 entries. Exact decoding reconstructs the selected
  successor, not necessarily the original source.
- **Track B: composition from descriptions.** Freeze vocabulary, mappings,
  candidate generator, scorer, search/stopping policy and compute before an
  independently reserved evaluation. Record first-attempt behavior, abstention,
  costs and independent correctness. No Track B solver or evaluation is supplied
  by the current harness. Mapping a supplied correct source to IDs is Track A
  representation evidence, not autonomous assembly.

### Repeatable candidate-selection procedure

1. Diagnose one failure or cost cluster and state a falsifiable hypothesis.
   Freeze problem/family/alias/exposure identities, source and contract hashes,
   qualification receipts, candidate provenance, budgets and promotion criteria
   before observing the new outcomes.
2. Compare designed-only, mined-only and combined seeds. Each proposed piece
   needs exact source witnesses and applicable domain/effect/dependency
   contracts. A name such as "make a map" does not prove substitutability.
   Keep dense counters, sparse maps, queue layers and visited/color state distinct
   where their contracts differ. Unrepresentable seed sets retain their complete
   problem denominator; no free alphabet or hidden helper makes them pass.
3. Record a support matrix by distinct problem, source alternative and piece:
   exact marginal cost, overlap, dependencies and pair complementarity. Use
   add/delete/swap/rewrite neighborhoods and exact resegmentation. Keep a bounded
   exhaustive or already-available solver reference for small frozen pools;
   its bound is not a global semantic optimum.
4. Independently qualify new full programs before search eligibility. Charge all
   helper/import/operand/control/framing/decoder bytes. Low energy cannot override
   output, mutation/alias, numeric, complexity or protected-boundary failures.
   Preserve invalid, unreachable, high-cost and successful proposals with reasons,
   source IDs, scorer identity, seed, exact labels and elapsed compute.
5. Compare neural and non-neural guidance only when both exist, under matched
   candidate access, exact-evaluation/scorer-call caps and compute, with training
   and model storage visible. The present comparison computes every proposal's
   exact cost and tests offline ranking mechanics; it cannot prove search speedup.
6. Retain coverage/input/storage/readability Pareto tradeoffs, regressions and
   failed hypotheses. Confirm a proposed gain with a predeclared matched run and
   independent review before promotion. Readability proxies do not establish
   human memorability. Publication and BITS export remain separate approvals and
   deterministic qualification steps.

Repeated feedback is development exposure. Family/near-duplicate separation and
source/alias leakage checks precede a one-time frozen confirmation gate. Once
confirmation outcomes influence candidate selection, those examples become
exposed development in the next immutable version. They cannot be relabeled
unseen. Track B needs its own untouched population and judge.

A future trainable energy must pin feature inputs, objective, positive/negative
sampling, source/family splits, model/checkpoint identity and training/scoring
budgets. The local protocol gives a proposed first ranking objective. A handmade
cost function, untrained scorer interface or synthetic test is not a trained EBM.
No model download, expensive training, protected-data opening or automatic
promotion follows from this documentation.

[Energy-Based Transformers (Gladstone et al., 2025)](https://arxiv.org/abs/2507.02092)
learn an input/candidate compatibility energy and refine predictions through
energy minimization. [ALOE (Dai et al., 2020)](https://proceedings.neurips.cc/paper_files/paper/2020/hash/7612936dcc85282c6fa4dd9d4ffe57f1-Abstract.html)
learns discrete energy models with an auxiliary sampler that mimics local search.
These motivate a candidate for neural-guided composition under **4c**, and for
ranking source rewrites or vocabulary moves under **2b**. Neither publication
establishes a result for Gamma's flat-literal decoder or complete cost objective.

A falsifiable first comparison would replace only the proposal ranking in a
frozen finite source/library search with learned energy, retaining the same
legal moves, exact fixed-dictionary parsing, correctness gates and full costs.
Compare against current non-neural search and an unlearned ranking control under
matched candidate access, wall time and total compute. Record training cost and
model storage separately and inclusively; do not hide them in inference-only
numbers. Freeze vocabulary, permitted source alternatives, seeds, budgets,
independent splits and evaluation procedure before measuring outcomes. Proposal
ranking must not see held-out tests or solutions, and exposed development tasks
cannot become unseen evaluation.

Measure qualified solutions found, full encoding costs, failed proposals,
search time and memory across seeds. For a later autonomous partial-assembly
study, independently qualify the complete decoded program from its description;
ranking an existing supplied answer does not demonstrate autonomous synthesis.
A low learned energy is neither a correctness certificate nor a global-optimality
bound. Any gain must survive matched ablations and independent output/effect and
decoding checks. A future execution contract and resource authorization are
required before training or running this new method.

## Completed development evidence

The [aggregate report](research-loop-v1/RESULTS.md) records the matched 150-program
JavaScript and separate 25-program Python checkpoints, including mixed outcomes,
difficulty provenance, exact packet costs and qualification limits. The
[four-source flow diagnostic](research-loop-v1/evidence/flow-aggregate.json)
completed after the protocol freeze: its pool is dominated by overlapping
wrapper strings, and exact restricted optimization does not beat the greedy
control. This is a useful candidate-generation failure, not a global bound.

Public artifacts include methods, synthetic solver fixtures, aggregates and
hash commitments. Private source programs, test inputs, dictionaries, encoded
sequences and detailed traces are not redistributed. The public package alone
cannot reproduce the corpus results; hash commitments are not substitute data.
That reproducibility gap remains an explicit unmet M6 gate. No autonomous
assembly, protected generalization, frozen 500 qualification or novel published
scientific finding is established.

## M6: publication-worthy novel discovery — proposed gate

M6 adds a research-quality target after the existing milestones without changing M1–M5. It is not achieved by meeting a compression threshold alone, by combining familiar terms, by writing a paper draft, or by obtaining a favorable small development result.

A candidate discovery must pass all of these gates:

1. **Precise contribution and prior-art distinction.** State the mechanism, its domain and a falsifiable explanation of why it helps. Compare the actual mechanism against applicable tokenization, grammar/library-learning and equivalent-program methods, including ConvexTok and Casel where relevant. Distinguish a new result within Gamma from a defensible contribution beyond known methods.
2. **Attributable improvement or substantive new finding.** Use predeclared matched strong baselines, separate source/dictionary/joint ablations, fair compute and complete costs. Retain negative results, regressions and rival explanations. A useful impossibility/bound/counterexample claim needs its own valid argument; failed heuristic search is insufficient.
3. **Correctness and representation integrity.** Independently reconstruct outputs, validate semantics and complexity obligations, and charge every code/structural/decoder dependency. Claims about cyclic/recursive formats require termination and resource guarantees. Finite testing is labeled as such; formal claims require proofs or checkable certificates.
4. **Scope and external validity.** Freeze new evaluation populations before outcomes; include multiple relevant families and both language tracks when the claim is cross-language. Do not reuse exposed source/case optimization as unseen solving evidence. Generalization claims require independently authored reserved evaluation and all failures retained.
5. **Reproducibility and review.** Preserve exact code/data/dictionary/sequence identities, environment, search budget, solver tolerances/bounds, executable checks and a complete experimental account. Seek an independent reproduction and adversarial review appropriate to the claim. Release only material authorized for publication; private sources and protected evidence remain protected.
6. **Publication decision.** Produce a readable manuscript/artifact draft explaining the contribution, limitations and comparison scope. Root/owner review decides whether to submit or publish. This document authorizes neither submission, external messaging, deployment nor a public Git push; acceptance by a venue cannot be promised.

If a gate fails, feed the evidence back into the next frozen experiment. A smaller, well-supported result can be retained without promoting it to M6. No numerical M1–M5 gate is relaxed to make a publication story easier.
