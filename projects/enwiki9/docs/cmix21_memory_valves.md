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
| 129,552 | `cmix21_text_mmap_paq5_ppmd129552k_fxcmassoc10tight92_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,407 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 44,928 | `cmix21_text_mmap_paq5_ppmd44928k_fxcmassoc10tight92_fxcmidx13full_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,404 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_minmaps_v1` | 1,000,000 | 736,961 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard2_minmaps_v1` | 250,000 | 609,849 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard3_minmaps_v1` | 250,000 | 609,858 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard4_minmaps_v1` | 250,000 | 609,937 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard5_allocpad_minmaps_v1` | 1,000,000 | 739,802 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard5_minmaps_v1` | 1,000,000 | 739,780 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard_minmaps_v1` | 1,000,000 | 737,781 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 25,600 | `cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 24,576 | `cmix21_text_mmap_paq5_ppmd24m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,804 | missing | 1,638,153 | 2,202,426 | true | missing | missing | `results/cmix21_text_mmap_paq5_ppmd24m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-23T203949.json` |
| 23,552 | `cmix21_text_mmap_paq5_ppmd23m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,804 | missing | 1,638,134 | 2,202,407 | true | missing | missing | `results/cmix21_text_mmap_paq5_ppmd23m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-24T101836.json` |
| 22,528 | `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_arena1_v1` | 1,024 | 564,570 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 22,528 | `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_mallocrss_v1` | 1,024 | 564,738 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 22,528 | `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,806 | missing | 1,638,101 | 2,202,376 | true | missing | rss fail (36 KiB over; tree 116,792 KiB over) | `results/cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-26T114711.json` |
| 22,400 | `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,807 | rss pass (41,788 KiB margin) | 1,638,083 | 2,202,359 | true | rss pass (2,748 KiB margin; tree 37,448 KiB over) | rss fail (68 KiB over; tree 116,576 KiB over) | `results/cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-28T005909.json` |
| 22,272 | `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,806 | rss pass (41,788 KiB margin) | 1,638,114 | 2,202,389 | true | rss pass (2,908 KiB margin; tree 37,132 KiB over) | rss fail (36 KiB over; tree 116,792 KiB over) | `results/cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-29T012252.json` |
| 21,888 | `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | rss pass (41,912 KiB margin) | 1,638,182 | 2,202,456 | true | rss pass (3,292 KiB margin; tree 36,868 KiB over) | rss fail (36 KiB over; tree 116,600 KiB over) | `results/cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-29T183814.json` |
| 21,760 | `cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,804 | rss pass (41,788 KiB margin) | 1,638,204 | 2,202,477 | true | rss pass (3,512 KiB margin; tree 36,612 KiB over) | rss fail (72 KiB over; tree 116,700 KiB over) | `results/cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-30T164613.json` |
| 21,632 | `cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | rss pass (41,916 KiB margin) | 1,638,229 | 2,202,503 | true | rss pass (3,516 KiB margin; tree 36,740 KiB over) | rss fail (68 KiB over; tree 116,824 KiB over) | `results/cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-01T123224.json` |
| 21,504 | `cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | n/a | n/a | missing | 1,638,165 | 2,202,438 | true | rss pass (3,644 KiB margin; tree 36,876 KiB over) | rss fail (72 KiB over; tree 116,828 KiB over) | `results/cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-02T060615.json` |
| 21,504 | `cmix21_text_mmap_paq5_ppmd21m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | rss pass (41,916 KiB margin) | n/a | n/a | n/a | rss pass (3,516 KiB margin; tree 25,340 KiB over) | missing | n/a |
| 21,376 | `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | rss pass (41,788 KiB margin) | 1,638,098 | 2,202,372 | true | rss pass (3,772 KiB margin; tree 36,136 KiB over) | rss fail (116 KiB over; tree 116,672 KiB over) | `results/cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-03T062324.json` |
| 21,248 | `cmix21_text_mmap_paq5_ppmd21248k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | rss pass (41,916 KiB margin) | 1,638,222 | 2,202,496 | true | rss pass (868 KiB margin; tree 36,356 KiB over) | rss fail (64 KiB over; tree 116,940 KiB over) | `results/cmix21_text_mmap_paq5_ppmd21248k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-06T060100.json` |
| 21,120 | `cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | rss pass (41,912 KiB margin) | 1,638,145 | 2,202,419 | true | rss pass (3,900 KiB margin; tree 36,172 KiB over) | rss fail (36 KiB over; tree 116,764 KiB over) | `results/cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-08T121005.json` |
| 20,992 | `cmix21_text_mmap_paq5_ppmd20992k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,804 | rss pass (38,860 KiB margin) | 1,638,161 | 2,202,434 | true | rss pass (1,228 KiB margin; tree 35,912 KiB over) | rss fail (68 KiB over; tree 116,796 KiB over) | `results/cmix21_text_mmap_paq5_ppmd20992k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-09T075239.json` |
| 20,864 | `cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,806 | rss pass (41,784 KiB margin) | 1,638,076 | 2,202,351 | true | rss pass (1,128 KiB margin; tree 35,840 KiB over) | rss fail (68 KiB over; tree 116,820 KiB over) | `results/cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-10T042446.json` |
| 20,736 | `cmix21_text_mmap_paq5_ppmd20736k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,000,000 | 738,805 | rss pass (41,788 KiB margin) | n/a | n/a | n/a | rss pass (13,116 KiB margin; tree 15,564 KiB over) | missing | n/a |
| 20,608 | `cmix21_text_mmap_paq5_ppmd20608k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,521 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,480 | `cmix21_text_mmap_paq5_ppmd20480k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,519 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | 1,000,000 | 738,785 | rss pass (1,654,584 KiB margin) | 1,638,340 | 2,202,600 | true | rss pass (1,614,424 KiB margin) | missing | `results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/2026-07-12T005633.json` |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_dense43_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,447 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 250,000 | 609,324 | rss pass (913,468 KiB margin) | 1,638,173 | 2,202,319 | true | rss pass (878,396 KiB margin) | missing | `results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-27T194640.json` |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_xz_v1` | 1,024 | 475,978 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10frt_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 565,377 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 250,000 | 609,339 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_fxcmidx13full_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,405 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,521 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 250,000 | 609,451 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,224 | `cmix21_text_mmap_paq5_ppmd20224k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,520 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 20,096 | `cmix21_text_mmap_paq5_ppmd20096k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,520 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 11,776 | `cmix21_text_mmap_paq5_ppmd11776k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,522 | missing | n/a | n/a | n/a | missing | missing | n/a |
| 1,024 | `cmix21_text_mmap_paq5_ppmd1024k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 1,024 | 564,520 | missing | n/a | n/a | n/a | missing | missing | n/a |

## Decimal 10GB Risk

The local runner enforces the binary `10GiB` single-process guard. This table
recomputes the same receipts against a stricter decimal `10GB` ceiling:

```text
decimal_10gb_guard_kib = 9,765,625
```

| PPMD cap KiB | Candidate | 1M decimal RSS | 10M decimal RSS | 100M decimal RSS |
|---:|---|---|---|---|
| 129,552 | `cmix21_text_mmap_paq5_ppmd129552k_fxcmassoc10tight92_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 44,928 | `cmix21_text_mmap_paq5_ppmd44928k_fxcmassoc10tight92_fxcmidx13full_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_minmaps_v1` | missing | missing | missing |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard2_minmaps_v1` | missing | missing | missing |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard3_minmaps_v1` | missing | missing | missing |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard4_minmaps_v1` | missing | missing | missing |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard5_allocpad_minmaps_v1` | missing | missing | missing |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard5_minmaps_v1` | missing | missing | missing |
| 40,960 | `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard_minmaps_v1` | missing | missing | missing |
| 25,600 | `cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 24,576 | `cmix21_text_mmap_paq5_ppmd24m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 23,552 | `cmix21_text_mmap_paq5_ppmd23m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 22,528 | `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_arena1_v1` | missing | missing | missing |
| 22,528 | `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_mallocrss_v1` | missing | missing | missing |
| 22,528 | `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | over (720,171 KiB over; tree 836,927 KiB over) |
| 22,400 | `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,347 KiB over; tree 699,259 KiB over) | over (717,387 KiB over; tree 757,583 KiB over) | over (720,203 KiB over; tree 836,711 KiB over) |
| 22,272 | `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,347 KiB over; tree 699,195 KiB over) | over (717,227 KiB over; tree 757,267 KiB over) | over (720,171 KiB over; tree 836,927 KiB over) |
| 21,888 | `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,223 KiB over; tree 699,323 KiB over) | over (716,843 KiB over; tree 757,003 KiB over) | over (720,171 KiB over; tree 836,735 KiB over) |
| 21,760 | `cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,347 KiB over; tree 699,195 KiB over) | over (716,623 KiB over; tree 756,747 KiB over) | over (720,207 KiB over; tree 836,835 KiB over) |
| 21,632 | `cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,219 KiB over; tree 699,319 KiB over) | over (716,619 KiB over; tree 756,875 KiB over) | over (720,203 KiB over; tree 836,959 KiB over) |
| 21,504 | `cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | over (716,491 KiB over; tree 757,011 KiB over) | over (720,207 KiB over; tree 836,963 KiB over) |
| 21,504 | `cmix21_text_mmap_paq5_ppmd21m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,219 KiB over; tree 699,187 KiB over) | over (716,619 KiB over; tree 745,475 KiB over) | missing |
| 21,376 | `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,347 KiB over; tree 699,319 KiB over) | over (716,363 KiB over; tree 756,271 KiB over) | over (720,251 KiB over; tree 836,807 KiB over) |
| 21,248 | `cmix21_text_mmap_paq5_ppmd21248k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,219 KiB over; tree 699,451 KiB over) | over (719,267 KiB over; tree 756,491 KiB over) | over (720,199 KiB over; tree 837,075 KiB over) |
| 21,120 | `cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,223 KiB over; tree 699,103 KiB over) | over (716,235 KiB over; tree 756,307 KiB over) | over (720,171 KiB over; tree 836,899 KiB over) |
| 20,992 | `cmix21_text_mmap_paq5_ppmd20992k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (681,275 KiB over; tree 701,363 KiB over) | over (718,907 KiB over; tree 756,047 KiB over) | over (720,203 KiB over; tree 836,931 KiB over) |
| 20,864 | `cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,351 KiB over; tree 699,331 KiB over) | over (719,007 KiB over; tree 755,975 KiB over) | over (720,203 KiB over; tree 836,955 KiB over) |
| 20,736 | `cmix21_text_mmap_paq5_ppmd20736k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | over (678,347 KiB over; tree 699,251 KiB over) | over (707,019 KiB over; tree 735,699 KiB over) | missing |
| 20,608 | `cmix21_text_mmap_paq5_ppmd20608k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,480 | `cmix21_text_mmap_paq5_ppmd20480k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | within (934,449 KiB margin; tree 913,521 KiB margin) | within (894,289 KiB margin; tree 854,193 KiB margin) | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_dense43_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | within (193,333 KiB margin; tree 172,381 KiB margin) | within (158,261 KiB margin; tree 117,361 KiB margin) | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_xz_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10frt_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_fxcmidx13full_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,352 | `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,224 | `cmix21_text_mmap_paq5_ppmd20224k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 20,096 | `cmix21_text_mmap_paq5_ppmd20096k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 11,776 | `cmix21_text_mmap_paq5_ppmd11776k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |
| 1,024 | `cmix21_text_mmap_paq5_ppmd1024k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | missing | missing | missing |

## PPMD-Only Decimal Feasibility

This section asks whether the measured PPMD cap ladder alone can close the
decimal `10GB` memory gap. It uses `10M` single-process RSS guard receipts
when those receipts are available.

- Active/reference cap: `ppmd22400k` at `22,400` KiB.
- Active/reference `10M` max single RSS: `10,483,012` KiB.
- Active/reference decimal `10GB` margin: `-717,387` KiB.
- Observed cap span: `22,400` -> `20,352` KiB.
- Observed RSS drop across that span: `+875,648` KiB.
- Observed RSS drop per KiB cap cut: `427.5625` KiB/KiB.
- PPMD-only cap cut needed for decimal `10GB`: `1,678` KiB.
- Projected PPMD cap after that cut: `20,722` KiB.
- PPMD-only feasibility verdict: `possible by slope`; validate with exact gates before promotion.
- Certificate active scope at render time: `10,000,000` bytes.

## Adjacent Archive Delta

| High cap KiB | Low cap KiB | Archive delta at 10M | Cap cut KiB | Bytes per KiB | Verdict |
|---:|---:|---:|---:|---:|---|
| 24,576 | 23,552 | -19 | 1,024 | -0.01855469 | await 100M receipt |
| 23,552 | 22,528 | -33 | 1,024 | -0.03222656 | lower cap still failed 100M RSS |
| 22,528 | 22,400 | -18 | 128 | -0.140625 | lower cap still failed 100M RSS |
| 22,400 | 22,272 | 31 | 128 | 0.2421875 | lower cap still failed 100M RSS |
| 22,272 | 21,888 | 68 | 384 | 0.1770833 | lower cap still failed 100M RSS |
| 21,888 | 21,760 | 22 | 128 | 0.171875 | lower cap still failed 100M RSS |
| 21,760 | 21,632 | 25 | 128 | 0.1953125 | lower cap still failed 100M RSS |
| 21,632 | 21,504 | -64 | 128 | -0.5 | lower cap still failed 100M RSS |
| 21,504 | 21,376 | -67 | 128 | -0.5234375 | lower cap still failed 100M RSS |
| 21,376 | 21,248 | 124 | 128 | 0.96875 | lower cap still failed 100M RSS |
| 21,248 | 21,120 | -77 | 128 | -0.6015625 | lower cap still failed 100M RSS |
| 21,120 | 20,992 | 16 | 128 | 0.125 | lower cap still failed 100M RSS |
| 20,992 | 20,864 | -85 | 128 | -0.6640625 | lower cap still failed 100M RSS |
| 20,864 | 20,352 | 264 | 512 | 0.515625 | await 100M receipt |
| 20,352 | 20,352 | -167 | 0 | n/a | await 100M receipt |

## Current Read

- `ppmd20864k` has the best exact `10M` archive in this ladder: `1,638,076`.
- `ppmd22m` has exact `10M` replay evidence but failed recorded `100M` RSS by `36` KiB. Decimal `10GB` overage would be `720,171` KiB.
- `ppmd22400k` has exact `10M` replay evidence but failed recorded `100M` RSS by `68` KiB. Decimal `10GB` overage would be `720,203` KiB.
- `ppmd22272k` has exact `10M` replay evidence but failed recorded `100M` RSS by `36` KiB. Decimal `10GB` overage would be `720,171` KiB.
- `ppmd21888k` has exact `10M` replay evidence but failed recorded `100M` RSS by `36` KiB. Decimal `10GB` overage would be `720,171` KiB.
- `ppmd21760k` has exact `10M` replay evidence but failed recorded `100M` RSS by `72` KiB. Decimal `10GB` overage would be `720,207` KiB.
- `ppmd21632k` has exact `10M` replay evidence but failed recorded `100M` RSS by `68` KiB. Decimal `10GB` overage would be `720,203` KiB.
- `ppmd21504k` has exact `10M` replay evidence but failed recorded `100M` RSS by `72` KiB. Decimal `10GB` overage would be `720,207` KiB.
- `ppmd21376k` has exact `10M` replay evidence but failed recorded `100M` RSS by `116` KiB. Decimal `10GB` overage would be `720,251` KiB.
- `ppmd21248k` has exact `10M` replay evidence but failed recorded `100M` RSS by `64` KiB. Decimal `10GB` overage would be `720,199` KiB.
- `ppmd21120k` has exact `10M` replay evidence but failed recorded `100M` RSS by `36` KiB. Decimal `10GB` overage would be `720,171` KiB.
- `ppmd20992k` has exact `10M` replay evidence but failed recorded `100M` RSS by `68` KiB. Decimal `10GB` overage would be `720,203` KiB.
- `ppmd20864k` has exact `10M` replay evidence but failed recorded `100M` RSS by `68` KiB. Decimal `10GB` overage would be `720,203` KiB.
- The next lower cap `40,960` KiB already has historical package rows (`ppmd40m`, `ppmd40m`, `ppmd40m`, `ppmd40m`, `ppmd40m`, `ppmd40m`, `ppmd40m`). A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.
- The next lower cap `22,528` KiB already has historical package rows (`ppmd22m`, `ppmd22m`, `ppmd22m`). A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.
- The next lower cap `21,504` KiB already has historical package rows (`ppmd21m`). A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.
- The next lower cap `20,352` KiB already has historical package rows (`ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`). A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.
- `ppmd20352k` is the active restarted ladder: latest exact prefix `250,000` scored `609,451`; active gate RSS status is missing. Certificate active gate is `10,000,000` bytes.
- The next lower cap `20,352` KiB already has historical package rows (`ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`, `ppmd20352k`). A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates.
- The next mutation should wait until the active restarted ladder records its current gate.
