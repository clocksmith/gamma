# Hutter transfer theorem bank

Status: `UNBOUND`

Competition status: inactive; solver distribution is not authorized

Score credit: zero

## Boundary

This document records seven proposed competition-grade mathematical problems.
They are materially different from the solved Atlas-Clockwork and ACS-PROVER
problems, but they are not themselves a Hutter Prize solution and are not an
active competition.

The missing implication is empirical and executable:

```text
accepted theorem witness
  -> frozen enwiki9 construction
  -> exact finite archive reduction
  -> complete package and framing ledger
  -> eligible runtime and memory
  -> exact full-1G score <= 108,000,000 bytes
```

Until the exact problem text, hidden finite transfer instance, verifier,
canonical tie rules, source package, and hashes are frozen, the bank remains
unbound. Even complete proofs of all seven general theorems would supply
prover infrastructure rather than the missing predictive information. Several
problem statements explicitly assume that a useful expert, teacher, quotient,
energy, event universe, or computation graph has already been supplied.

The current project boundary remains:

```text
target                         108,000,000 bytes
verified full-1G score         unknown
best counted forecast          109,389,323 bytes
remaining forecast debt          1,389,323 bytes
new score credit                         0 bytes
runtime eligibility            unresolved
```

## 1. Exact finite-precision Bayesian envelope

Given `K >= 2` causal binary experts with probabilities on the finite grid
`{1, ..., M - 1} / M` and positive rational priors, construct a deterministic
bounded-integer Bayesian mixture coupled to an exact binary arithmetic coder.

The requested theorem must provide:

1. Encoder-decoder identity for posterior state and emitted probabilities.
2. The ideal bound
   `L_mix <= L_k - log2(pi_k)` for every expert `k`.
3. A realized archive bound
   `8|A_int| <= min_k(L_k - log2(pi_k)) + R(n,K,M) + F`, with explicit
   finite-precision penalty `R` and exact finalization bound `F`.
4. Sharp examples or a matching lower bound for `R`.
5. A characterization of exact baseline-archive identity.
6. Canonical serialization, overflow bounds, and exact operation counts.
7. A specialization to sleeping experts that equal the baseline outside
   their active regions.

Transfer boundary: this certifies a supplied same-stream probability family.
A global mixture cannot beat the better whole-stream expert merely because of
the envelope theorem. Local complementarity must already be present in a
baseline-backed sleeping expert, and the exact archive plus implementation
cost must beat matched selectors. The rejected Typed Event Sleeping Bayes
realization is not reopened by proving this theorem.

## 2. Delayed sleeping residual-program retrieval

At time `t`, let a decoder-visible process expose a finite set `C_t` of
fixed-horizon probability programs made only from completed past data. Programs
become visible after delay `d`; the baseline is always available.

Construct a deterministic fixed-point online algorithm and prove, for a
comparator with at most `S` switches,

```text
L_alg <= L_comp + R(N,S,d,n) + n epsilon_q,
```

with exact constants and an explicit quantization penalty. The theorem must
also cover encoder-decoder identity, entry/sleep/expiry/eviction, bounded
memory, canonical ties and eviction, exact operation counts, unavoidable
regret terms, and a baseline-backed specialization with no loss outside active
opportunities.

Transfer boundary: this governs use of a residual-program universe only after
that universe has empirical headroom. The exact SRSTC candidate-universe and
zero-command log-opinion constructions are terminal rejections, so this
theorem cannot reopen their frozen horizon, key language, or program family.
A new bound instance requires a materially different paying residual object.

## 3. Certified quotient distillation of a contractive predictor

Let compact state space `S` carry rational symbol transitions `F_a` that are
`rho`-contractive, `rho < 1`, and an `L`-Lipschitz output logit. A supplied
finite quotient consists of cells, representatives, deterministic transitions,
certified transition error at most `delta`, and output error at most `epsilon`.

Prove uniform state shadowing and cumulative binary-logistic loss transfer in
terms only of `rho`, `delta`, `epsilon`, `L`, `n`, initial error, and integer
quantization. Supply a finite interval-arithmetic verifier, an exact integer
realization, sufficient precision, sharp or supremally sharp examples,
failure conditions without contraction or coverage, and a canonical
refinement procedure returning either a certificate or a violating
cell-transition witness.

Transfer boundary: the theorem deliberately does not discover a useful
teacher or partition. It becomes operational only after a causal teacher has
target-scale headroom, a contractive bounded realization, and a quotient whose
certified regret plus package cost retains enough gain. The active NNCP gate
can establish only the first, zero-credit teacher antecedent.

## 4. Exact output-equivalence summaries for finite transducers

For a deterministic finite-state transducer, summarize block `u` by the vector

```text
Sigma_u(s) = (f_u(s), o_u(s)),
```

where both the final state and exact emitted byte string are retained for each
starting state.

Prove associative composition; contextual replaceability exactly when
complete summaries agree; final archive-byte identity rather than cost
identity; canonical minimal acyclic prefix/suffix-DAG representation of the
state-indexed output strings; direct canonical-DAG composition; balanced point
and fixed-length interval replacement; exact size and time bounds; a locally
checkable whole-stream identity certificate; and counterexamples showing that
equal final state and equal total cost do not imply equal bytes.

Transfer boundary: this strengthens exact recomposition and identity proof for
a supplied finite transducer. It does not select a profitable replacement or
create a better probability source. A bound instance must identify a concrete
archive transducer and replacement family whose exact output summaries can be
computed within the package and resource ledger.

## 5. Parity-constrained B-best decoding on factor graphs

For binary vector `x`, integer factor energy
`E(x) = sum_alpha phi_alpha(x_{S_alpha})`, syndrome `Hx = s`, and a supplied
tree decomposition of the combined primal graph of width `w`, enumerate the
first `B` feasible vectors in increasing `(E(x), x_lex)` order.

Prove exact duplicate-free enumeration, a
`2^{O(w)} poly(n,k,B)` bound, recovery of the rank of a supplied feasible
vector when at most `B`, canonical first-hit and locally verifiable dynamic
programming certificates, exact memory bounds, all boundary cases, and an
appropriate lower-bound family showing unavoidable exponential dependence on
`w`.

Transfer boundary: this supplies bounded search only after a causal residual
energy ranks truth sufficiently early and the combined factor/parity graph has
small width. It does not create low energy rank, a useful prototype, or cheap
syndromes. No current enwiki9 instance establishes these antecedents.

## 6. Exact time-memory Pareto frontier for series-parallel DAGs

Given a rooted two-terminal series-parallel computation DAG with integer node
compute times, output sizes, and scratch sizes, enumerate the complete
nondominated `(peak memory, total compute time)` frontier when schedules may
retain, free, and recompute intermediate outputs.

Prove exact series and parallel recurrences; correct retained/recomputed
semantics; completeness and realizability; safe dominance pruning; a canonical
schedule for every point; pseudopolynomial complexity under a supplied integer
budget; local schedule certificates; zero-size, zero-cost, and shared-terminal
boundary cases; and counterexamples separating this result from tree-only
ordering theorems.

Transfer boundary: this optimizes an abstract supplied DAG. It neither proves
that endpoint428 or a child has such a DAG nor substitutes for measured
process-tree RSS and reference-calibrated CPU time. A bound instance must map
every node to exact native work and memory, prove the series-parallel model,
and replay the chosen schedule archive-identically.

## 7. Exact MDL selection of causal reversible events

Given a finite stream and supplied events with intervals, decoder-visible
triggers, reversible reconstruction rules, payload costs, rule identifiers,
and one-time rule-description costs, select nonoverlapping events with literal
fallback. Jointly optimize the legal parse, active rules, literal regions, and
an integer binary prefix code whose lengths depend on final event counts. The
event-overlap graph comes with a width-`w` tree decomposition.

Prove existence, the lexicographically first optimum, exact prefix-code
construction, an explicit fixed-parameter bound such as
`2^{O(w)} poly(n)`, a locally verifiable certificate, correct zero-use and
zero-length-codeword handling, a perturbation bound for approximate costs, and
a counterexample to greedy maximum-gain selection under shared descriptions
and prefix costs.

Transfer boundary: profitable causal reversible events are supplied, not
discovered. The theorem can optimize a future WIKI event universe only after
its causal candidate construction and actual finite side/residual costs are
frozen. It cannot turn the current free WIKIFORWARD narrative ceiling or a
failed LOGOS/TESSERA universe into score credit.

## Binding requirements

A problem may leave `UNBOUND` only when one versioned package contains:

1. Exact public problem text and SHA-256.
2. A hidden finite enwiki9 transfer instance and hash commitment.
3. A proved theorem-witness-to-executable-witness compiler.
4. Canonical serialization, ordering, ties, and failure semantics.
5. A decidable local verifier plus exact expected pass conditions.
6. Complete archive, source, table, framing, runtime, and memory accounting.
7. A numeric implication from every accepted witness to a named target-bearing
   gate on an identical population.
8. A final path from that gate to native 10M, disjoint, 100M, and full-1G
   replay.

The binding must be strong enough that an accepted solution discharges a
specific remaining compressor antecedent rather than merely making research
easier. If data collection, model discovery, benchmark execution, package
construction, or runtime qualification remains, that work belongs to the
organizer and must not be disguised as a mathematical competition.

## Operational disposition

- Preserve the bank as mathematical research infrastructure.
- Do not create adaptive proposals or queue jobs for the general theorems.
- Do not distribute them as `ACS-MATH-SEAL-2` or imply that seal is bound.
- Bind only a theorem whose exact empirical antecedents already pass and whose
  remaining obstruction is genuinely mathematical.
- Continue the active NNCP teacher gate and the frozen WIKIBACK-to-WIKI-JOINT
  empirical sequence; those experiments search for the information the
  theorems assume.

