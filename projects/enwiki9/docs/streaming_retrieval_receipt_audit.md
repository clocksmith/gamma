# Streaming Retrieval Receipt Audit

This report audits cached SRSTC shadow receipts. It is not a compressor
benchmark and does not mutate the active cmix21 runner.

Promotion rule:

```text
positive_net_shadow is evidence, not promotion.
promotion requires held-out gain, no alignment warning, bounded state,
and complete block-regression evidence.
```

## Summary

- Receipts scanned: `0`
- Positive net receipts: `0`
- Promotion-ready shadow receipts: `0`
- Max block regression cap: `0` bytes
- Max online state cap: `64,000,000` bytes

## Objective Selection

This is the SRSTC generator-verifier-selector loop in receipt form:
candidate receipts are generated separately, verified by held-out
same-coder bytes, then selected by net bytes after counted costs
and promotion blockers.

- Current winner score: `110,793,128`
- Best forecast score: `110,181,114`
- Target score: `109,500,000`
- Public-record gap to target: `1,293,128` bytes
- Forecast gap to target: `681,114` bytes
- Recommended action: `generate_more_shadow_receipts_before_packaging`
- Reason: `no positive promotion-ready receipt is available`
- Target-substrate receipts: `0`
- Positive-net target-substrate receipts: `0`
- Replay-ready target-substrate receipts: `0`

## Top Rows

| Receipt | Net Saved | Held-out Saved | State Bytes | Block Audit | Largest Regression | Ready | Blockers |
|---|---:|---:|---:|---|---:|---|---|

## Readout

- A positive net receipt can justify more shadow work.
- Raw-shadow promotion readiness does not prove additive transfer onto fx2 or cmix21.
- Packaging requires a positive counted target-substrate replay, not only a raw-shadow win.
- Existing receipts without full block rows should be regenerated with complete block diagnostics before packaging.
