# cmix21 Memory Surface Scan

Generated from saved cmix21 result JSONs and RSS guard receipts. This report
is lock-safe: it does not launch compression and does not mutate candidates.

Claim rule:

```text
Rows here identify existing evidence and missing evidence for memory surfaces.
They do not prove a target result and do not replace exact gate promotion.
```

## Active Gate Context

- Active candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Active scope bytes: `250,000`
- cmix21 candidates with result or guard evidence: `69`

## Observed Knob Values

- PPMD caps KiB: `20352`, `20480`, `20608`, `20736`, `20864`, `20992`, `21120`, `21248`, `21376`, `21504`, `21632`, `21760`, `21888`, `22272`, `22400`, `22528`, `23552`, `24576`, `25600`, `35840`, `40960`, `51200`, `61440`, `71680`, `75776`, `76800`, `102400`
- PAQ levels: `5`, `9`
- FXCM-RCM values: `2`, `4`, `8`, `16`, `20`, `21`, `22`, `24`, `28`
- RCM values: `32`
- Buffer tokens: `buffull`, `bufsixtyfourth`, `bufthirtysecond`
- Guard token sets: `abovecellguard,dualsparseguard,match2guard,stemguard`, `dualsparseguard,match2guard,stemguard`, `dualsparseguard,matchguard,stemguard`, `matchguard,sparseguard,stemguard`, `matchguard,stemguard`, `ppmdguard`, `ppmdguard2`, `ppmdguard3`, `ppmdguard4`, `ppmdguard5`, `stemguard`
- Match token sets: `match2guard`, `matchdiv2`, `matchguard`

## Surface Evidence Rows

| Candidate | PPMD KiB | PAQ | FXCM-RCM | RCM | Buffer | Guards | Latest prefix | Prefix archive | 10M archive | 10M RSS | 100M RSS |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 20,352 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,024 | 247 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufsixtyfourth_minmaps_v1` | 40,960 | 5 | n/a | 32 | bufsixtyfourth | n/a | 1,000,000 | 174,395 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_minmaps_v1` | 40,960 | 5 | 20 | 32 | bufsixtyfourth | n/a | 1,000,000 | 174,396 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard_minmaps_v1` | 40,960 | 5 | 20 | 32 | bufsixtyfourth | ppmdguard | 1,000,000 | 174,396 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | abovecellguard,dualsparseguard,match2guard,stemguard | 1,000,000 | 174,398 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | dualsparseguard,match2guard,stemguard | 1,000,000 | 174,398 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | dualsparseguard,matchguard,stemguard | 1,000,000 | 174,399 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | matchguard,stemguard | 1,000,000 | 174,399 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | matchguard,sparseguard,stemguard | 1,000,000 | 174,399 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_stemguard_rcm32_bufthirtysecond_minmaps_v1` | 102,400 | 5 | n/a | 32 | bufthirtysecond | stemguard | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd35m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | 35,840 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | 40,960 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd50m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | 51,200 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd60m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | 61,440 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd70m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | 71,680 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd74m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | 75,776 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd75m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | 76,800 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,415 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | 20,352 | 5 | 20 | 32 | buffull | ppmdguard2 | 1,000,000 | 174,525 | 1,638,340 | pass; bin +1,614,424 KiB; dec +894,289 KiB | missing |
| `cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 25,600 | 5 | n/a | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,527 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_ppmdsq_rcm32_bufthirtysecond_minmaps_v1` | 25,600 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,527 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd35m_fxcmidx13div2_allocsafe_rcm32_bufthirtysecond_minmaps_v1` | 35,840 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,527 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd35m_fxcmidx13div2_ppmdsq_rcm32_bufthirtysecond_minmaps_v1` | 35,840 | 5 | n/a | 32 | bufthirtysecond | n/a | 1,000,000 | 174,527 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard5_allocpad_minmaps_v1` | 40,960 | 5 | 20 | 32 | bufsixtyfourth | ppmdguard5 | 1,000,000 | 174,527 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard5_minmaps_v1` | 40,960 | 5 | 20 | 32 | bufsixtyfourth | ppmdguard5 | 1,000,000 | 174,527 | n/a | missing | missing |
| `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm21_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 22,528 | 5 | 21 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,529 | n/a | pass; bin +2,780 KiB; dec -717,355 KiB | missing |
| `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm22_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 22,528 | 5 | 22 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,529 | n/a | pass; bin +2,876 KiB; dec -717,259 KiB | missing |
| `cmix21_text_mmap_paq5_ppmd20736k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 20,736 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | n/a | pass; bin +13,116 KiB; dec -707,019 KiB | missing |
| `cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 20,864 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,076 | pass; bin +1,128 KiB; dec -719,007 KiB | fail; bin -68 KiB; dec -720,203 KiB |
| `cmix21_text_mmap_paq5_ppmd20992k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 20,992 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,161 | pass; bin +1,228 KiB; dec -718,907 KiB | fail; bin -68 KiB; dec -720,203 KiB |
| `cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 21,120 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,145 | pass; bin +3,900 KiB; dec -716,235 KiB | fail; bin -36 KiB; dec -720,171 KiB |
| `cmix21_text_mmap_paq5_ppmd21248k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 21,248 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,222 | pass; bin +868 KiB; dec -719,267 KiB | fail; bin -64 KiB; dec -720,199 KiB |
| `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 21,376 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,098 | pass; bin +3,772 KiB; dec -716,363 KiB | fail; bin -116 KiB; dec -720,251 KiB |
| `cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 21,632 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,229 | pass; bin +3,516 KiB; dec -716,619 KiB | fail; bin -68 KiB; dec -720,203 KiB |
| `cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 21,760 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,204 | pass; bin +3,512 KiB; dec -716,623 KiB | fail; bin -72 KiB; dec -720,207 KiB |
| `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 21,888 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,182 | pass; bin +3,292 KiB; dec -716,843 KiB | fail; bin -36 KiB; dec -720,171 KiB |
| `cmix21_text_mmap_paq5_ppmd21m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 21,504 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | n/a | pass; bin +3,516 KiB; dec -716,619 KiB | missing |
| `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 22,272 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,114 | pass; bin +2,908 KiB; dec -717,227 KiB | fail; bin -36 KiB; dec -720,171 KiB |
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 22,400 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,083 | pass; bin +2,748 KiB; dec -717,387 KiB | fail; bin -68 KiB; dec -720,203 KiB |
| `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 22,528 | 5 | 20 | 32 | bufthirtysecond | ppmdguard2 | 1,000,000 | 174,531 | 1,638,101 | missing | fail; bin -36 KiB; dec -720,171 KiB |

## Readout

- PPMD cap is well-instrumented, but the decimal `10GB` gap is too large for PPMD-only cuts on current receipts.
- Non-PPMD surfaces with existing evidence include PAQ level, FXCM-RCM depth, RCM size, buffer token, match tokens, and guard variants.
- The next memory mutation after the active gate should use this scan with exact guard receipts; do not infer admissibility from names alone.