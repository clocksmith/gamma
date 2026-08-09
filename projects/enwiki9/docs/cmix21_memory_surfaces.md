# cmix21 Memory Surface Scan

Generated from saved cmix21 result JSONs and RSS guard receipts. This report
is lock-safe: it does not launch compression and does not mutate candidates.

Claim rule:

```text
Rows here identify existing evidence and missing evidence for memory surfaces.
They do not prove a target result and do not replace exact gate promotion.
```

## Active Gate Context

- Active candidate: `nncp_libnc_trainlen32_mature_1998848_qm2_v1`
- Active scope bytes: `1,998,848`
- cmix21 candidates with result or guard evidence: `9`

## Observed Knob Values

- PPMD caps KiB: `20352`, `76800`, `102400`
- PAQ levels: `5`
- FXCM-RCM values: `20`, `28`
- RCM values: `32`
- Buffer tokens: `buffull`, `bufthirtysecond`
- Guard token sets: `ppmdguard2`
- Match token sets: n/a

## Surface Evidence Rows

| Candidate | PPMD KiB | PAQ | FXCM-RCM | RCM | Buffer | Guards | Latest prefix | Prefix archive | 10M archive | 10M RSS | 100M RSS |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1` | 76,800 | 5 | 28 | 32 | bufthirtysecond | n/a | 1,000,000 | 174,423 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_densebudget96_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 20,352 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,533 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 20,352 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,536 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | n/a | 250,000 | 44,978 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osxz_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | n/a | 250,000 | 44,978 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | n/a | 250,000 | 45,184 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_xz_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | n/a | 250,000 | 45,184 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_xzstrip_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | n/a | 250,000 | 45,184 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | 20,352 | 5 | 20 | 32 | buffull | ppmdguard2 | n/a | n/a | n/a | missing | pass; bin +1,588,440 KiB; dec +868,305 KiB |

## Readout

- PPMD cap is well-instrumented, but the decimal `10GB` gap is too large for PPMD-only cuts on current receipts.
- Non-PPMD surfaces with existing evidence include PAQ level, FXCM-RCM depth, RCM size, buffer token, match tokens, and guard variants.
- The next memory mutation after the active gate should use this scan with exact guard receipts; do not infer admissibility from names alone.