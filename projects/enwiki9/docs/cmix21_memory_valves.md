# cmix21 PPMD Memory-Valve Report

Generated from saved result JSONs and RSS guard receipts.

Claim rule:

```text
This report measures one memory surface: the PPMD cap.
Rows are exact only for the measured scope.
A 100M RSS pass would still not prove a full 1G target result.
```

## Candidate Ladder

| PPMD cap KiB | Candidate | Latest sub-10M scope | Latest sub-10M score | 1M RSS | 10M archive | 10M score | 10M determinism | 10M RSS | 100M RSS | 10M result |
|---:|---|---:|---:|---|---:|---:|---|---|---|---|
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | n/a | n/a | missing | n/a | n/a | n/a | missing | rss pass (1,588,440 KiB margin) | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,682 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_densebudget96_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 250,000 | 609,377 | missing | n/a | n/a | n/a | missing | missing | n/a |

## Decimal 10GB Risk

The local runner enforces the binary `10GiB` single-process guard. This table
recomputes the same receipts against a stricter decimal `10GB` ceiling:

```text
decimal_10gb_guard_kib = 9,765,625
```

| PPMD cap KiB | Candidate | 1M decimal RSS | 10M decimal RSS | 100M decimal RSS |
|---:|---|---|---|---|
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | missing | missing | within (868,305 KiB margin; tree 747,677 KiB margin) |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_densebudget96_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |

## PPMD-Only Decimal Feasibility

This section asks whether the measured PPMD cap ladder alone can close the
decimal `10GB` memory gap. It uses `10M` single-process RSS guard receipts
when those receipts are available.

- Not enough `10M` guard receipts exist to estimate a PPMD-only memory slope.

## Adjacent Archive Delta

| High cap KiB | Low cap KiB | Archive delta at 10M | Cap cut KiB | Bytes per KiB | Verdict |
|---:|---:|---:|---:|---:|---|

## Current Read

- The next lower cap `20,352` KiB already has historical package rows (`ppmd20352k`, `ppmd20352k`, `ppmd20352k`). A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.
- `ppmd20352k` is the active restarted ladder: latest exact prefix `1,000,000` scored `738,682`; active gate RSS status is missing.
- The next lower cap `20,352` KiB already has historical package rows (`ppmd20352k`, `ppmd20352k`). A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.
- The next mutation should wait until the active restarted ladder records its current gate.
