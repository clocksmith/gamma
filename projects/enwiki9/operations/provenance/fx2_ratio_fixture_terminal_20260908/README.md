# Native FX2 residual ratio fixture result

[Terminal audit](../fx2_ratio_fixture_terminal_20260908.json),
[four-arm index](index.json), and
[validated reflection](../../adaptive/reflections/20260908T190345Z_1e4e5a7eee.json)
describe the same closed comparison. P/K/D produce 3,223 bytes; S produces
3,236 bytes. All independently reconstruct the exact 50,051-byte public fixture,
repeat deterministically, and agree at every recorded coder and introduced
calibration-state boundary. This is not a corpus confirmation or prize score.

D changes 64,583 quantized bit predictions, with diagnostic ideal savings of
-1.747438686 bits and zero actual archive savings. The local overlapping
source/binary/options inventory increases by 22,746 bytes. Complete submission
accounting remains unresolved. This fixed realization fails its gain predicate.

The [frozen runner](../../../tools/fx2_residual_ratio_fixture50051_q0_v3.py)
and [experiment](../../adaptive/experiments/fx2_residual_ratio_fixture50051_q0_v3.json)
retain source identities, exact commands, resource bounds, and controls.
Per-phase execution receipts under
`results/fx2_residual_ratio_fixture50051_q0_v3/` record encode, independent
decode, repeat, and trace-disabled encode commands. Native prediction code
remained unchanged across the two preceding runner-only implementation retries.

Validate and idempotently inspect the canonical ledger recording from the
project directory:

```bash
python3 tools/record_driver_result.py fx2_residual_ratio_fixture50051_q0_v3 \
  --terminal-index operations/provenance/fx2_ratio_fixture_terminal_20260908/index.json --check
```

The [trace retention manifest](../fx2_ratio_fixture_trace_retention_20260908.json)
maps twelve immutable raw state traces to four content-addressed gzip files.
Their combined publication size is 40,474,775 bytes. For an absent raw trace,
verify the compressed file's SHA256, decompress to the recorded path using
exclusive creation, and verify its length and raw SHA256. Never replace an
existing trace. The raw local files remain intact; each gzip was independently
decompressed and hash-checked before recording. These diagnostic bytes are
experiment evidence, not decoder dependencies.

Next research must diagnose an attributable prediction cost before choosing
one successor with fresh frozen inputs. Scaling this zero-gain fixture is not
authorized by its result. No unrelated MIDAS or HORIZON evidence changed.

[Posthoc loss attribution](../fx2_ratio_fixture_loss_attribution_20260908.json)
finds chronological-third ideal savings of +1.4465, -0.6799 and -2.5140 bits.
The effect is not consistently positive. Hindsight bins by the probability of
the actual truth locate losses, but cannot serve as decoder-visible selectors
or identify a causal parameter. These diagnostics do not justify a parameter
sweep or larger launch by themselves.
