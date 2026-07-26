# Residual Certificate Report

> Superseded as an active target by `docs/target_revision_20260725.md`. Historical target arithmetic below is preserved.

This report tracks the certificate-first path toward the 10.95% target. It is
not a leaderboard claim. It records whether a causal residual correction explains
enough of `fx2`'s remaining log-loss to justify building a production candidate.

## Target Ledger

Current calibrated production path:

```text
S_baseline = 110,181,114
S_target   = 109,500,000
debt       =     681,114 bytes = 5,448,912 bits
```

A residual state machine clears the target only if:

```text
residual_gain_bits - added_code_bits >= 5,448,912
```

Projected gain from a prefix is only a discovery signal. A constructive proof
requires exact causal coverage of the scored stream or a conservative count-based
certificate that covers the missing bits.

## Tested Shape

Residual rows are emitted by an `fx2-cmix` build compiled with
`FX2_RESIDUAL_LOG=1`. For each encoded bit, the logger records the baseline
probability and deterministic structural state derived from already observed
history. `fx2_residual_apm_score.py` then applies a causal KT/APM correction:

```text
key = selected state tuple
p_corrected = blend(p_fx2, p_KT(key))
```

The correction predicts from current counts, emits corrected log-loss, then
updates with the realized bit. This avoids future leakage.

## 64K Probe

Probe label:

```text
residual_apm_64k_field_mode_full
```

Initial key:

```text
p_bucket,bit_pos,field,mode
```

Measured result:

```text
raw bytes requested       65,536
residual rows scored     301,808 bits
baseline loss            108,837.304688 bits
corrected loss           108,811.566406 bits
exact gain                    25.738281 bits
projected 1G gain             85,280 bytes
target debt                  681,114 bytes
```

Verdict: positive signal, insufficient target coverage.

## 64K Key Sweep

The strongest completed sweep result was:

```text
key          p_bucket,bit_pos,mode,char_class
blend_ppm    50000
contexts     4444
gain_bits    44.039
projection   145,918 bytes at 1G
```

Tied key:

```text
p_bucket,bit_pos,field,mode,char_class
```

Verdict: stronger than the initial field/mode key, still below the 681,114-byte
debt before code cost.

## 64K Oracle Upper Bound

The oracle scanner asks a different question: if a per-state calibration table
were perfect after seeing the rows, is there enough residual bias in the state
family to matter?

Best raw oracle signal before table cost:

```text
key                p_bucket,bit_pos,mode,char_class
contexts           4,444
oracle gain        3,259.901 bits
```

With a 16-bit table-entry cost, this prefix is negative because the table is
larger than the measured prefix gain. With zero table cost, this says the state
family has theoretical calibration headroom, but the tested causal KT/APM
coupling does not extract it.

## Promotion Rule

Promote this residual APM family only if a larger exact probe shows a material
gain-slope increase and the projection approaches the target debt:

```text
projected_gain_bytes >= 681,114 + added_code_bytes
```

If the 1M promotion probe remains below target scale, mark this exact coupling
as `measured_negative` evidence and move to a different coupling, not a wider
cross-product of the same weak state.

## Active Promotion Probe

The promotion probe used the best 64K key:

```text
label       residual_apm_1m_mode_charclass_b050
limit       1,000,000
key         p_bucket,bit_pos,mode,char_class
blend_ppm   50000
```

Measured result:

```text
raw bytes requested        1,000,000
residual rows scored       4,805,936 bits
compressed archive           175,614 bytes
baseline loss            1,403,892.613281 bits
corrected loss           1,403,613.664062 bits
exact gain                     278.949219 bits
projected 1G gain              58,043 bytes
target debt                   681,114 bytes
```

Exact shadow-coder sanity check:

```text
tool                 fx2_shadow_residual_coder.py
encoded rows         4,805,936 bits
baseline same-coder    175,577 bytes
shadow coder           175,575 bytes
saved bits                  13
saved bytes                  2
unique contexts          5,038
```

Decision:

- The gain slope weakened from the 64K sweep projection.
- The exact same-coder delta is only 2 bytes on the 1M residual stream.
- This exact KT/APM residual coupling is not a 10.95 path.
- Keep the residual logger and certificate tools.
- Prune `p_bucket,bit_pos,*` KT/APM correction crosses from active search unless
  a new correction rule changes the probability model, not merely the key width.

Next residual direction:

```text
Do not widen the same APM key.
Test a different coupling: calibrated SSE-style residual table, typed-anchor
state inside fx2 update contexts, or a count-based structural certificate.
```

## Related Typed-Anchor Soft-State Prunes

The narrow typed-anchor soft-SSE probes have already resolved at the 250K gate:

```text
fx2_typed_anchor_soft_field_sse_v1       archive 45,338
fx2_typed_anchor_soft_mode_sse_v1        archive 45,338
fx2_typed_anchor_soft_field_mode_sse_v1  archive 45,338
promotion floor                          archive 45,331
```

All three are `measured_negative`. They should remain as historical evidence,
but they should not be used as active parents unless the coupling changes from
soft-SSE coordinate injection to a materially different update rule.
