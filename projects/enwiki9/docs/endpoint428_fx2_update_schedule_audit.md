# endpoint428 FX2 update-schedule audit

Status: source-level no-bug finding. No compressor mutation and no score credit.

The exact recovered endpoint428 source was inspected after parent identity was
reproduced. The apparent "FX2 double update" is not two updates of one model
state.

`Predictor::Perceive` performs these distinct operations once per truth bit:

1. `fx2lite_endpoint428::Perceive(...)` schedules the independent endpoint
   branch update.
2. The compact CMIX model loop skips `fxcm_index_`.
3. After the compact byte mixer has produced `lstmpr` and `lstmex`, the compact
   `models_[fxcm_index_]` state is updated exactly once.

The endpoint branch owns a separate `Fx2LiteFXCM` instance and updates it once
inside `Endpoint::PerceiveSync`. The Makefile compiles that branch with symbol
renames including `FXCM=Fx2LiteFXCM`, `fxcmv1=fx2lite_fxcmv1`,
`lstmpr=fx2lite_lstmpr`, and `lstmex=fx2lite_lstmex`. Its object file exports
the renamed globals, not the compact branch globals. The two FXCM builds also
use different compound-context divisors: compact `CMIX_FXCM_CMC2_DIV=2` and
endpoint `FX2LITE_CMC2_DIV=4`.

The recovered source therefore contains two independent ensemble experts,
each advanced once, rather than one state accidentally advanced twice.
Removing either update would change the endpoint428 algorithm and must be
evaluated as expert deletion, not described as a correctness correction.
Existing FX2 freeze experiments already cover reduced training/update work and
do not establish target-bearing archive gain.

Decision: do not create a silent FX2 "double-update fix." The next compression
experiment must change the information source or coded representation.

Evidence:

- `docs/typed_event_sleeping_bayes_envelope_plan.md`
- `results/typed_event_sleeping_bayes_parent_recovery_q0_v1/decision.json`
- exact recovered source under
  `/home/x/enwiki9-nonproof/results/endpoint428_pair_layer0_gate_dot_fuse_output_update_loop_lzma_source_package_v1/clean-build-a/build/`
- `results/endpoint428_fx2_snapshot_freeze_campaign_v1/decision.json`
