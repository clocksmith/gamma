# Native forward boundary for fixed P/E

The next correction uses the unchanged pinned native predictor as the forward
implementation, freshly exporting current model tensors on every call. This
removes the separate Torch forward computation from the values used to evaluate
the training objective. Both logits and probabilities come from native execution.
No recorded native intermediates are inputs, and no predictor source is modified.

The backward path is deliberately separate: the existing CPU reference supplies
a whole-model surrogate Jacobian. Torch's softmax Jacobian is evaluated at native
logits, while forward probability values remain the actual native probabilities.
This is an approximate gradient, not native differentiation, an exact derivative
of quantization/archive size, or a claim that Torch's internal states now match.
Its quality for optimization remains empirical. No optimizer is constructed here.

`NativeForward` takes an explicit binary identity, workspace, current model,
export template, tokens, reset markers and FP16 priors. A new child reloads freshly
exported tensors and cold state every call. A custom autograd function returns
native bytes directly and routes only the adjoint into the surrogate; subtraction
and re-addition would risk floating cancellation. Loss rejects a different token
population and excludes piece-end and final unpaired positions.

[Plan](../operations/provenance/fx2_native_forward2048_q0_v1_plan.json),
[experiment](../operations/adaptive/experiments/fx2_native_forward2048_q0_v1.json),
[closure](../operations/provenance/fx2_native_forward2048_q0_v1_closure.json), and
[synthetic preflight](../operations/provenance/fx2_native_forward_synthetic_20260919.json)
bind the correction. The candidate is `fx2_native_forward2048_q0_v1`, owner
`codex-native-forward-20260919`. Reuse the existing bounded numerical gate;
the new tool remains a thin compatibility entrypoint.

The preflight compares P, E and P again on eight synthetic tokens. Every one of
the 410 output values per input row is bit-identical to the previous independent
native replay. All434 freshly exported tensors match the decoded native identities.
Each P/E backward check yields429 finite, nonzero parameter-gradient tensors and
leaves parameters unchanged. Two focused exact-value/adjoint tests and the143-test
architecture group pass. This establishes neither gradient quality nor native
agreement on the full retained-input fixture yet.

The frozen gate repeats this on the same2,048 retained native input rows as the
previous attribution, with actual reset markers and2,043 scored positions. It
compares every forward value, rather than only the first64 traced rows. Run P/E/P
in that order to detect checkpoint or recurrent-state reuse. Expected outputs
enter the validator only after the native forward call. Two synthetic backward
checks occur, with zero updates; real-input evaluation does no backward pass.

Acceptance requires bitwise equality of logits/probabilities, all434 tensor
identities, exact P repeat, unchanged parameters and finite nonzero synthetic
gradients. There is no tolerance for forward values. Only the final FP64 loss
summation order allows an absolute1e-10-bit difference. A failure stops without
training, checkpoint selection, feature additions or population expansion.
CPU3,4GB resident memory,1GB scratch,no swap and1,800-second wall stop bound the
job. The96M complete-byte target remains unchanged, with zero score credit here.

After the gate closes, record the exact parity result, guard, reflection and
canonical diagnostic rows. A subsequent data-only versus joint-cost training
comparison needs its own matched-window budget and frozen selection rules;
finite native archives and packed files remain authoritative.
