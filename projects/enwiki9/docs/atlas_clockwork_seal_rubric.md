# Rubric for the Atlas, Clockwork, and Seal Examination

## 1. Grading model

The examination is graded by strict verification rather than partial credit.

Every problem receives exactly one status:

```text
PASS
FAIL
INVALID
```

`PASS` means every mathematical inequality, construction requirement,
admissibility rule, and artifact check succeeds.

`FAIL` means the submission is well-formed but does not establish a required
inequality, resource bound, identity, or construction.

`INVALID` means the evidence is not admissible, an object is missing, a cost is
uncounted, or the verifier cannot reproduce the claimed calculation.

The examination passes only when all three problems receive `PASS`.

---

# 2. Global admissibility rules

## 2.1 Exactness

All probabilities, states, lengths, and resource counts must use exact integer
or rational semantics.

The following are inadmissible as final evidence:

- Floating-point probabilities.
- Approximate logarithms.
- Expected lengths.
- Sampled estimates.
- Prefix projections.
- Asymptotic bounds without finite-instance evaluation.
- Confidence intervals in place of exact quantities.

Floating-point arithmetic may be used during private search, but no submitted
object or proof may depend on it.

## 2.2 Complete accounting

The following must be represented and counted:

- Programs.
- Tables.
- Codebooks.
- Chamber labels.
- Framing.
- Length fields.
- Initialization.
- Exceptional cases.
- Alignment and padding.
- Arithmetic finalization.
- Model-selection information.
- Replacement or retained reference components.

Any uncounted information yields `INVALID`.

## 2.3 Information availability

Before each reconstructed symbol, the submitted machine may use only:

- Previously reconstructed symbols.
- Fixed represented programs and tables.
- Labels already read from the representation.
- State deterministically derived from these objects.

Using an unrevealed current or future symbol without first representing the
necessary label yields `INVALID`.

## 2.4 Joint replay

Savings from separately measured mechanisms may not be added.

Every claimed combined result must be measured through one exact replay of the
complete combined state trajectory.

Violation yields `INVALID`.

## 2.5 Uniformity

The submitted transition system must be uniform over positions.

Position-specific behavior is permitted only through explicitly represented
finite tables or programs.

An uncounted time-indexed trace, prediction stream, or position-specific
constant yields `INVALID`.

## 2.6 Reproducibility

Every machine-readable artifact must include:

- Byte length.
- SHA-256 hash.
- Format identifier.
- Dependency identifiers.
- Deterministic construction rule.

A missing or mismatching artifact yields `INVALID`.

---

# 3. Problem I rubric: The Atlas

## 3.1 Required artifacts

The submission must contain:

- `atlas.codebook`
- `atlas.dag`
- `atlas.label_model`
- `atlas.labels`
- `atlas.grammar_encoding`
- `atlas.controls`
- `atlas.interval_ledger`
- `atlas.causality_proof`
- `atlas.decision`

Equivalent names are permitted if the manifest maps them unambiguously.

## 3.2 Codebook validity

Verify:

- \(1\le K\le K_{\max}\).
- Every bias is within the supplied quantization range.
- Every weight is an allowed integer.
- Every sparsity bound is satisfied.
- Every activation mask has dimension \(m\).
- Every correction table is finite.
- Every codeword has a unique prefix-free grammar representation.

Any failure produces `INVALID`.

## 3.3 DAG validity

Verify:

- The graph is finite and acyclic.
- Every internal node tests one declared observable.
- Every leaf selects one valid correction state.
- Node, depth, and table bounds are satisfied.
- Evaluation order is deterministic.
- No node reads an unavailable coordinate.

Reading an unavailable coordinate produces `INVALID`.

Exceeding a structural bound produces `FAIL`.

## 3.4 Label legality

For every chamber \(I_j=H_j\Vert J_j\), verify:

- \(H_j\) is reconstructed before \(z_j\) is read.
- \(z_j\) is read before the first corrected symbol in \(J_j\).
- The probability used to represent \(z_j\) depends only on permitted history.
- Every label symbol is included in the interval ledger.
- Every label-model update is deterministic.

An illegal label placement produces `INVALID`.

## 3.5 Probability reconstruction

Two independent implementations must reconstruct every \(q_t\).

Require:

\[
q_t^{(1)}=q_t^{(2)}
\qquad
\text{for all }t.
\]

The verifier compares complete probability-trace hashes and performs direct
spot-independent full traversal.

Any disagreement produces `INVALID`.

## 3.6 Control verification

Recompute exact lengths for:

- \(Z_0\)
- \(Z_1\)
- \(Z_K\)
- \(Z_R\)
- \(Z_P\)

The controls must share the declared arithmetic and finalization semantics.

Control failure does not automatically fail the Atlas inequality, but a
missing or non-comparable control produces `INVALID`.

## 3.7 Atlas inequality

Recompute:

\[
L_{\mathrm{Atlas}}
=
\mathcal A_Q(y_{\mathcal H};\pi_{\mathcal H})
+
K_\Gamma(\mathcal H).
\]

Problem I passes exactly when:

\[
L_{\mathrm{Atlas}}\le L^\star-\Sigma.
\]

If the construction is valid but the inequality fails, return `FAIL`.

---

# 4. Problem II rubric: The Clockwork

## 4.1 Required artifacts

The submission must contain:

- `clockwork.transition`
- `clockwork.output`
- `clockwork.initial_state`
- `clockwork.tables`
- `clockwork.grammar_encoding`
- `clockwork.interval_ledger`
- `clockwork.operation_ledger`
- `clockwork.memory_ledger`
- `clockwork.degradation_ledger`
- `clockwork.uniformity_proof`
- `clockwork.decision`

## 4.2 Integer-circuit validity

Verify:

- Every operation belongs to the permitted word-RAM instruction set.
- Every intermediate value has a declared width.
- Overflow behavior is defined.
- Signedness is defined.
- Shift behavior is defined.
- Rounding and saturation are defined.
- Lookup bounds are proved.
- Exceptional paths terminate.

Undefined behavior produces `INVALID`.

## 4.3 Uniformity verification

Verify:

- One transition circuit applies to every position.
- One output circuit applies to every position.
- Every position-dependent value is read from a represented table.
- The sealed object is not embedded in an uncounted constant sequence.
- No teacher trace is required during final execution.

A hidden position-dependent trace produces `INVALID`.

## 4.4 Probability verification

Reconstruct the complete \(\widehat q_t\) sequence independently.

Require:

\[
\widehat q_t^{(1)}=\widehat q_t^{(2)}
\qquad
\text{for all }t.
\]

Any disagreement produces `INVALID`.

## 4.5 Degradation accounting

Recompute:

\[
\Delta_{\mathrm{total}}
=
L_{\mathrm{Clock}}-L_{\mathrm{Atlas}}.
\]

The degradation ledger must reconcile:

- Probability changes.
- Program additions.
- Program removals.
- Table additions.
- Table removals.
- Label changes.
- Framing changes.
- Finalization changes.

An unreconciled bit produces `INVALID`.

## 4.6 Operation bound

Recompute the exact or valid worst-case operation count:

\[
\operatorname{Ops}_{\mathfrak M_w}
(\widehat F,\widehat G,x).
\]

Count every operation performed during:

- Initialization.
- Label processing.
- State transitions.
- Probability production.
- Interval updates.
- Exceptional paths.
- Finalization.

Problem II requires:

\[
\operatorname{Ops}\le T_{\max}.
\]

Average or expected operation counts are inadmissible.

## 4.7 Memory bound

Recompute the peak number of simultaneously live words:

\[
\operatorname{PeakWords}_{\mathfrak M_w}
(\widehat F,\widehat G,x).
\]

Count:

- Static tables resident in memory.
- Dynamic state.
- Arithmetic state.
- Label state.
- Temporary buffers.
- Recursion or stack state.
- Exceptional-path allocations.

Problem II requires:

\[
\operatorname{PeakWords}\le M_{\max}.
\]

## 4.8 Clockwork inequality

Recompute:

\[
L_{\mathrm{Clock}}
=
\mathcal A_Q(y_{\mathcal H};\widehat\pi)
+
K_\Gamma(\widehat F,\widehat G,\widehat{\mathcal H}).
\]

Problem II passes exactly when:

\[
L_{\mathrm{Clock}}-L_{\mathrm{Atlas}}\le\Sigma,
\]

\[
\operatorname{Ops}\le T_{\max},
\]

and

\[
\operatorname{PeakWords}\le M_{\max}.
\]

A valid construction missing any inequality receives `FAIL`.

---

# 5. Problem III rubric: The Seal

## 5.1 Required artifacts

The submission must contain:

- `seal.manifest`
- `seal.bitstring`
- `seal.encoder`
- `seal.decoder`
- `seal.grammar_encoding`
- `seal.field_ledger`
- `seal.interval_ledger`
- `seal.operation_ledger`
- `seal.memory_ledger`
- `seal.induction_proof`
- `seal.roundtrip_receipt`
- `seal.reencode_receipt`
- `seal.verifier`
- `seal.decision`

## 5.2 Self-delimitation

Verify that every field is:

- Prefix-free, or
- Assigned a length determined entirely by earlier fields.

The decoder must locate every boundary without external information.

Ambiguous framing produces `INVALID`.

## 5.3 Initialization identity

Before decoding the first represented symbol, verify that encoder and decoder
have identical:

- Grammar version.
- Word width.
- Probability denominator.
- Initial predictive state.
- Initial label state.
- Initial interval state.
- Tables and codebook.

Any mismatch produces `INVALID`.

## 5.4 Inductive identity

For every reconstructed position \(t\), verify:

\[
\text{encoder state}_t=\text{decoder state}_t,
\]

\[
q_t^{E}=q_t^{D},
\]

\[
\text{interval}_t^{E}=\text{interval}_t^{D}.
\]

After reconstructing \(x_t\), verify identical updates on both sides.

Failure at any position produces `FAIL` if the programs are otherwise
well-defined, or `INVALID` if behavior is undefined.

## 5.5 Roundtrip

Compute:

\[
W_1=E(x),
\]

\[
x'=D(W_1).
\]

Require:

\[
x'=x.
\]

Byte inequality produces `FAIL`.

## 5.6 Canonical re-encoding

Compute:

\[
W_2=E(x').
\]

Require:

\[
W_2=W_1.
\]

Any difference produces `FAIL`.

## 5.7 Final length

Recompute:

\[
L_{\mathrm{final}}
=
|W_1|
+
K_\Gamma(E,D).
\]

The field ledger must sum exactly to \(|W_1|\). The program ledger must sum
exactly to \(K_\Gamma(E,D)\).

Problem III requires:

\[
L_{\mathrm{final}}\le L^\star.
\]

## 5.8 Final resource bounds

Recompute:

\[
\operatorname{Ops}(E,x),
\qquad
\operatorname{Ops}(D,W_1),
\]

\[
\operatorname{PeakWords}(E,x),
\qquad
\operatorname{PeakWords}(D,W_1).
\]

Require:

\[
\operatorname{Ops}(E,x)\le T_{\max},
\]

\[
\operatorname{Ops}(D,W_1)\le T_{\max},
\]

\[
\operatorname{PeakWords}(E,x)\le M_{\max},
\]

\[
\operatorname{PeakWords}(D,W_1)\le M_{\max}.
\]

## 5.9 Determinism

The verifier rejects dependence on:

- Thread scheduling.
- Unordered iteration.
- Filesystem ordering.
- Wall-clock timing.
- Randomness without a represented seed.
- Floating-point behavior.
- Uninitialized memory.
- Platform-dependent overflow.

Any such dependency produces `INVALID`.

---

# 6. Independent verifier contract

The independent verifier receives only:

- The public finite instance.
- The submitted manifest.
- The submitted machine-readable artifacts.

It must not access a network, hidden model, external table, or private
execution trace.

It performs:

1. Format and hash validation.
2. Grammar decoding.
3. Atlas reconstruction.
4. Atlas interval replay.
5. Clockwork reconstruction.
6. Clockwork interval replay.
7. Resource-ledger verification.
8. Encoder execution.
9. Decoder execution.
10. Canonical re-encoding.
11. Final length reconciliation.
12. Final decision.

Its terminal output is one of:

```text
VALID
FAIL PROBLEM_I <condition>
FAIL PROBLEM_II <condition>
FAIL PROBLEM_III <condition>
INVALID <condition>
```

`VALID` is emitted only if every requirement in this rubric passes.

---

# 7. Final acceptance theorem

The verifier emits `VALID` only after establishing:

\[
L_{\mathrm{Atlas}}\le L^\star-\Sigma,
\]

\[
L_{\mathrm{Clock}}-L_{\mathrm{Atlas}}\le\Sigma,
\]

\[
D(E(x))=x,
\]

\[
E(D(E(x)))=E(x),
\]

\[
|E(x)|+K_\Gamma(E,D)\le L^\star,
\]

\[
\operatorname{Ops}(E),\operatorname{Ops}(D)\le T_{\max},
\]

and

\[
\operatorname{Memory}(E),\operatorname{Memory}(D)\le M_{\max}.
\]

All three problems must pass. A failure or invalid result in any problem fails
the examination.
