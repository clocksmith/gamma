# cmix21 Memory Surface Scan

Generated from saved cmix21 result JSONs and RSS guard receipts. This report
is lock-safe: it does not launch compression and does not mutate candidates.

Claim rule:

```text
Rows here identify existing evidence and missing evidence for memory surfaces.
They do not prove a target result and do not replace exact gate promotion.
```

## Active Gate Context

- Active candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Active scope bytes: `100,000,000`
- cmix21 candidates with result or guard evidence: `1`

## Observed Knob Values

- PPMD caps KiB: `20352`
- PAQ levels: `5`
- FXCM-RCM values: `20`
- RCM values: `32`
- Buffer tokens: `buffull`
- Guard token sets: `ppmdguard2`
- Match token sets: n/a

## Surface Evidence Rows

| Candidate | PPMD KiB | PAQ | FXCM-RCM | RCM | Buffer | Guards | Latest prefix | Prefix archive | 10M archive | 10M RSS | 100M RSS |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | 20,352 | 5 | 20 | 32 | buffull | ppmdguard2 | n/a | n/a | n/a | missing | running; terminal margin pending |

## Readout

- PPMD cap is well-instrumented, but the decimal `10GB` gap is too large for PPMD-only cuts on current receipts.
- Non-PPMD surfaces with existing evidence include PAQ level, FXCM-RCM depth, RCM size, buffer token, match tokens, and guard variants.
- The next memory mutation after the active gate should use this scan with exact guard receipts; do not infer admissibility from names alone.