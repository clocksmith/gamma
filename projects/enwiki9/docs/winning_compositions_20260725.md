# Gamma enwiki9 Winning-Composition Candidates - 2026-07-25

## Claim Boundary

These are unproved project candidates, not winning results or publication-level
novelty claims. They operationalize the hypothesis that the missing mechanism is
an interaction among selected slices rather than one standalone algorithm.
Every proposal, oracle, and shadow row receives zero score credit until exact
finite-precision replay, counted package accounting, roundtrip, and measured-
scope transfer exist.

## Composition Rule

For components `A`, `B`, and `C`, run the complete subset lattice:

```text
baseline
A  B  C
AB AC BC
ABC
```

Define exact measured gain relative to the same baseline as:

```text
G(S) = baseline_bytes - candidate_bytes(S)
```

Pair and three-way interaction terms are:

```text
I(A,B)   = G(AB) - G(A) - G(B)
I(A,B,C) = G(ABC) - G(AB) - G(AC) - G(BC)
           + G(A) + G(B) + G(C)
```

A slice may lose alone. It remains eligible only when its removal from the full
composition causes a reproducible loss on development and sealed holdout, its
marginal contribution exceeds its package and runtime cost, and the interaction
does not depend on one opening-prefix population. This supersedes the prior rule
that every component must first win independently.

The target hierarchy is:

```text
engineering checkpoint              109,000,000
minimum prize-competitive gate      108,500,000
canonical design target             108,000,000
current counted forecast            109,389,323
canonical design-target debt          1,389,323
```

## C01: Wheeler Phase Tensor Retriever

Components:

```text
A07  Wheeler Equivalence Retrieval
B09  Soft Changepoint Context Bank
B07  Tensor-Train Residual Circuit
```

Fusion:

1. Wheeler retrieval exposes exact candidate WRT continuations from previously
   decoded corpus history.
2. The changepoint posterior supplies soft page-phase, topic-age, and style-age
   weights that control candidate eligibility and forgetting without hard resets.
3. A tiny tensor train scores interactions among retrieval evidence, phase
   posterior, structural role, base probability, and exact candidate prefix.
4. A protected base escape preserves endpoint probabilities whenever retrieval
   evidence is absent or harmful.

Why the interaction could matter:

```text
Wheeler alone       retrieves too many weakly related continuations
phase alone         routes existing information without adding evidence
tensor alone        models interactions but has no new continuation source
combined            retrieves new evidence, selects its regime, scores its fit
```

Experiment ladder:

```text
C01-O  truth-aware continuation ceiling, zero score credit
C01-S  frozen causal probability shadow over all eight subsets
C01-E  exact finite-precision replay of frozen winning subset
C01-I  bounded Wheeler/wavelet implementation only after O, S, and E pass
```

Promotion gate:

```text
truth-aware distant-window ceiling       >= 1,500 B/M
canonical 10M exact net replay           >= 2,100 B/M
opening, offset, random pages            positive
package, memory, and runtime              fully counted
largest page regression                   bounded and explained
```

Kill when candidate recall is high but causal ranking cannot transfer, tensor
contraction erases index speed, or the full composition does not beat every
proper subset after counted costs.

## C02: Selective Tensor State Replacement

Components:

```text
B06  Householder Selective State Coder
B07  Tensor-Train Residual Circuit
B09  Soft Changepoint Context Bank
```

Fusion:

1. Input-dependent write and decay gates maintain compact scalar state channels.
2. Signed Householder reflections create branch-light full-rank interaction
   without a dense recurrent matrix.
3. A tiny tensor train converts selected state, WRT phase, parser role, base
   probability, and byte-prefix features into an exact residual logit.
4. The changepoint posterior modulates forgetting and state resets across page
   phases rather than adding another standalone prediction lane.

Why the interaction could matter:

```text
Householder alone   stores and mixes state but has a weak output surface
tensor alone        captures feature products without durable selective memory
phase alone         changes adaptation rate but adds no representation
combined            compact memory, nonlinear readout, uncertainty-aware timescale
```

This is a replacement architecture. It must remove selected recurrent, SSE,
mixer, or indirect-prediction work; running beside the complete endpoint is not
an eligible result.

Experiment ladder:

```text
C02-T  frozen trace readout test for tensor and phase slices
C02-N0 reduced native endpoint control
C02-N1 equal-capacity changed-stream replacement
C02-F complete seven-subset plus baseline factorial replay
```

Promotion gate:

```text
exact roundtrip and deterministic archive     required
counted projection                            <= 108,000,000
decoder memory                                below decimal 10GB guard
controlled decode runtime                     materially lower than N0
component cycle attribution                   proves actual work replacement
full combination                              beats every proper subset net
```

Kill when Householder updates cost more cycles than removed recurrence, tensor
rank grows beyond packed-state economics, or changepoint modulation duplicates
existing decay schedules.

## C03: Orbit-Phase Parallel MDL Coder

Components:

```text
A05  Symmetry-Orbit Realization Coder
A11  Parallel MDL Page-Phase Coder
B09  Soft Changepoint Context Bank
```

Fusion:

1. A paid page-local first pass selects a compact context tree, phase hazards,
   and profitable exact realization orbits.
2. The transmitted page model initializes independently decodable segments.
3. Soft changepoint state chooses phase-conditioned contexts without requiring
   a brittle explicit discourse parse.
4. Orbit coding shares statistics across case, apostrophe, hyphen-space,
   numeric, quoting, and approved spelling transformations while transmitting
   the exact action and residual.
5. Segments decode in parallel and concatenate into the original WRT stream.

Why the interaction could matter:

```text
MDL alone           pays model cost without enough page-specific structure
orbit alone         offers small gains but little runtime improvement
phase alone         improves boundaries without parallel execution
combined            paid page model amortized by parallel phase and orbit reuse
```

Experiment ladder:

```text
C03-O  exact orbit joint-codelength oracle
C03-P  paid page-model and phase descriptor accounting
C03-N0 reduced serial page predictor
C03-N1 equal-capacity parallel composition
C03-F complete subset lattice with identical page population
```

Promotion gate:

```text
all page model and segment framing bytes       counted
exact WRT and raw roundtrip                     required
counted projection                             <= 108,000,000
controlled encode and decode runtime           materially below N0
short, long, template-heavy, prose-heavy       positive transfer
parallel finalization overhead                 explicitly counted
```

Kill when orbit savings fail to repay their model fields, page phases do not
improve context selection, segment redundancy dominates parallel speed, or the
full composition loses to a simpler proper subset.

## Normalized Order

```text
0  close XML21 certification
1  C01-O Wheeler continuation ceiling
2  C01-S Wheeler-phase-tensor causal subset lattice
3  C02-T tensor/phase trace screen
4  C02-N0/N1 selective-state replacement
5  C03-O symmetry-orbit oracle
6  C03 paid-model and parallel replacement controls
```

C01 has the highest new-score potential. C02 is the strongest joint score and
runtime replacement. C03 is the lower-ceiling but potentially cheaper
runtime-oriented composition. No full implementation begins before its cheapest
oracle or trace gate passes.
