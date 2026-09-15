# Native attention-window mutation

The hidden-signature cache activated but saved no archive bytes. Its configuration
is retired. The next experiment changes information available inside the native
predictor: the three attention layers retain 2,048 prior input tokens instead of
1,024. Nine KDA layers, trained weights, positional encoding, PPMd, mixer learning,
preprocessing, and arithmetic coding remain as authored in the trimmed parent.
Changed neural predictions can intentionally change later mixer state.

This is an unmeasured mutation of an existing architecture, not a novelty theorem
or a claimed Hutter result. Longer context could be redundant with recurrent
memory or harm a model trained with the original window.

## Exact implementation boundary

Only two source constants change: optimized `model_opt.cpp`'s `WIN` and
`opt/attn.h`'s `ATTN_WIN`, both from 1024 to 2048. Source preimage hashes are checked.
The original trained-model header and weights stay byte-identical. Literal 1024
byte strides inside the blocked matrix kernel are untouched. The header's old
performance comments describe the upstream 1024-window benchmark; this document
describes the changed runtime geometry.

The existing reset receipt identifies 98 pieces, eight longer than 1,025 inputs.
Summing `max(0,L-1025)` gives 117,352 modeled positions beyond 1,024 prior inputs,
out of 151,210. This is exposure, not measured information gain. Use the entire
already exposed opening raw `[0,250000)` population, unchanged cold initialization,
and no window-length sweep. Independent confirmation remains sealed and unread.

## Controls and executable evidence

P is rebuilt from the 127-member trimmed source ZIP and must reproduce its exact
binary and 33,429-byte archive. D has the two changed constants. Rebuild both
after `make clean`, requiring identical repeated binaries within each arm. No
new required compile/run option or fitted parameter is introduced.

For each arm, encode with the built-in `--save-transformer-probs` observation,
independently decode without that option, encode again from restored raw input
with the observation, and encode unobserved from the original raw input. Require
all three archives identical within arm, raw equality, and both exported neural
streams identical. The observer is excluded from required execution options only
after unobserved archive identity is demonstrated.

The export records 205 half-precision probabilities after each completed input
byte. Row i predicts byte i+1; its final row predicts beyond the sample. Validate
exact row population and finite values. Across P/D, require row identity before
1,024 preceding inputs within every reset piece, and record the first changed
row and total changed rows. The 1,024th step can use different fixed/variable
kernel specialization, so the guaranteed comparison is the first 1,023 steps.
Do not claim complete model-state or decoder-tensor identity: those states are
not serialized. Independent native inverse, repeated neural output, fixed source
changes, and synthetic kernel tests establish the declared evidence boundary.

P/D is the controlled window-size ablation. Trace-on/off identity supplies the
bookkeeping control. No wrong-label specialist or output mixture is part of this
architecture experiment; no gains from those older candidates are inherited.

## Economics and execution

Measure actual native archives, rebuilt executable bytes, and reproducible source
ZIP bytes. Source and executable deltas are alternative component accounting
forms, never added together. Weights/dictionary are unchanged and remain counted
assets. Required option delta is zero. Complete submission form, platform and
licensing closure remain inherited unresolved questions, not a complete score.

Define `g=P.archive-D.archive`, `s=D.zip-P.zip`, `b=D.binary-P.binary`.
Report `g`, `g-s`, and `g-b` separately. Positive `g` and `g-s`, with all checks
passing, authorize an unchanged independent confirmation, not 1G. A loss closes
this 2048-window configuration without another length or retraining rescue.
Resource/evidence failures do not establish a compression loss.

There are sixteen native phases: four builds, three clean commands, one exact
preprocessing check, and four codec operations for each of P and D. CPU 2,
9,999,998,976 memory bytes, zero swap, 12,000,000,000 scratch bytes, and a
1,800-second total stop are the frozen discovery envelope. Timing is diagnostic.
The same native transient-file cleanup and process-tree checks apply per phase.

Six synthetic tests cover exact changed members and model preservation, source
ZIP reproduction, bit-identical prefix kernels, independent sliding averages
through fill/eviction, repeated random trajectories, and neural-stream boundary
validation. The initial probe passed an unaligned foreign output buffer into an
aligned-store kernel and crashed; a probe-local aligned temporary plus memcpy
fixes that ABI boundary. Its failed log is retained. Final tests deliberately
use unaligned foreign outputs. No corpus execution occurred during that repair.

The active objective is still 90,000,000 complete bytes. Full-corpus score is
unknown. No predicted saving is assigned to this mutation.
