# NNCP v3.3 LibNC update-state trajectory

Proposal and candidate: `nncp_v33_libnc_update_state_trajectory_v1`

## Provenance correction

`tools/nncp_libnc_save_hook.c` intercepts `nc_param_list_end` and saves the
seeded coefficient list before the first evaluation or update. The artifact
called `final_coefs` in the prior multi-update receipt is therefore an initial
state. Its comparison with the analytic eight-update state is invalid. The
native probability trace remains valid and still proves that the analytic
replay diverges beginning with the second four-symbol segment.

## One-change experiment

Build a temporary observation-only source variant. Immediately after every
`nc_sgd_opt_update` and `mem_update`, save:

```text
post-update parameter list
mem_h for every layer
train_h for every layer
```

Use the unchanged first 32 raw bytes, eight four-symbol updates, source seed,
profile, arithmetic coder, and teacher observer. Run the source twice and
require byte-identical archives, probability traces, parameter checkpoints,
and memory checkpoints.

Replay the same eight updates through the currently proved analytic graph and
record the corresponding parameter and memory state after every segment. The
comparison must identify the first update and tensor family at which source
and replay diverge. It must not use captured source state as replay input.

## Decision contract

The gate has zero score credit. A unique first divergence authorizes one
component-level child:

```text
parameters diverge first  -> localize gradient clipping or Adam update
memory diverges first      -> localize train_h/mem_h update semantics
state matches but P1 fails -> localize evolving-state forward operation order
```

Any observation patch that changes the bound archive or teacher trace is an
infrastructure failure. A valid localization or rejection exits zero. No
faithful-profile prefix, forecast change, or published-score inheritance is
authorized by this diagnostic alone.

## Frozen population

```text
raw bytes             32
symbols               32
segment length         4
updates                8
parameter tolerance    2e-5
memory tolerance       2e-6
probability tolerance  2e-5
```
