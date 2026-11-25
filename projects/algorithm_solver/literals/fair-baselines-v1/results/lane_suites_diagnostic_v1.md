# Lane suites diagnostic

Diagnostic only. The held-out halves of these suites were already used during the lane's design. BIT3 numbers are copied from the lane's committed results; BIT3 was not run.

Records: suite records exported by an earlier run of this script (--reuse-exported).

## Sizes

Like-for-like bytes (the lane's container form), with the difference from BIT3's committed number in brackets. The baselines were measured on the rebuilt record sets; where a rebuilt set differs from the committed one (see the per-suite notes), the bracketed difference is across two record sets.

| | `short_wgsl_vs_json_80_to_80` | `short_ts_vs_mjs_80_to_80` | `med_ts_vs_json_50_to_50` |
|---|---:|---:|---:|
| held-out records, raw bytes (rebuilt) | 160, 23,924 | 160, 24,245 | 100, 60,187 |
| held-out records, raw bytes (committed run) | 160, 23,837 | 160, 24,180 | 100, 58,759 |
| lane, committed: BIT3 | 12,092 (+0) | 12,390 (+0) | 30,109 (+0) |
| lane, committed: FSST-255 (lane's own implementation) | 14,618 (+2,526) | 14,929 (+2,539) | 37,646 (+7,537) |
| lane, committed: DEFLATE raw + dictionary | 12,842 (+750) | 13,458 (+1,068) | 27,664 (-2,445) |
| lane, committed: zstd -19 full frame + dictionary | 14,678 (+2,586) | 15,459 (+3,069) | 27,426 (-2,683) |
| this harness: `raw-indexed` | 24,574 (+12,482) | 24,895 (+12,505) | 60,597 (+30,488) |
| this harness: `zstd-frame-lane-rule` | 14,679 (+2,587) | 15,267 (+2,877) | 27,805 (-2,304) |
| this harness: `zstd-frame-tuned` | 14,031 (+1,939) | 15,155 (+2,765) | 27,519 (-2,590) |
| this harness: `zstd-lean-frame-tuned` | 12,751 (+659) | 13,867 (+1,477) | 26,619 (-3,490) |
| this harness: `zstd-raw-block-tuned` | 11,971 (-121) | 13,087 (+697) | 26,136 (-3,973) |
| this harness: `deflate-raw-lane-rule` | 12,865 (+773) | 13,164 (+774) | 28,064 (-2,045) |
| this harness: `deflate-raw-tuned` | 12,316 (+224) | 12,816 (+426) | 27,884 (-2,225) |
| this harness: `fsst-reference` | 14,084 (+1,992) | 14,576 (+2,186) | 38,474 (+8,365) |
| this harness: `fsst-lane-own-impl` | 14,699 (+2,607) | 14,867 (+2,477) | 38,686 (+8,577) |
| this harness: `zstd-lean-frame-tuned/per-group` | 12,733 (+641) | 13,871 (+1,481) | 26,555 (-3,554) |
| this harness: `zstd-raw-block-tuned/per-group` | 11,953 (-139) | 13,282 (+892) | 26,067 (-4,042) |
| this harness: `deflate-raw-tuned/per-group` | 12,298 (+206) | 13,579 (+1,189) | 27,955 (-2,154) |
| this harness: `fsst-reference/per-group` | 13,402 (+1,310) | 14,490 (+2,100) | 37,371 (+7,262) |
| this harness: `zstd-lean-frame-blocks-of-2` | 11,920 (-172) | 12,704 (+314) | 25,939 (-4,170) |
| this harness: `zstd-lean-frame-blocks-of-4` | 10,912 (-1,180) | 11,860 (-530) | 25,040 (-5,069) |
| this harness: `zstd-lean-frame-blocks-of-8` | 10,082 (-2,010) | 11,186 (-1,204) | 24,062 (-6,047) |
| this harness: `zstd-lean-frame-blocks-of-16` | 9,584 (-2,508) | 10,605 (-1,785) | 22,492 (-7,617) |

## Lookup time

Nanoseconds per single-record lookup, in memory, same loop for every method: loop mean (best round) / median of per-record means / 95th percentile of per-record means. One-minute load average of the machine when each suite finished: 19.91, 6.83, 7.76. The lane's committed ns/seek come from its own loop on another occasion and are listed only for reference.

| | `short_wgsl_vs_json_80_to_80` | `short_ts_vs_mjs_80_to_80` | `med_ts_vs_json_50_to_50` |
|---|---:|---:|---:|
| lane, committed (mean only): BIT3 | 227 | 226 | 889 |
| lane, committed (mean only): FSST-255 (lane's own implementation) | 50 | 53 | 194 |
| lane, committed (mean only): DEFLATE raw + dictionary | 513 | 374 | 1,387 |
| lane, committed (mean only): zstd -19 full frame + dictionary | 194 | 198 | 750 |
| this harness: `raw-indexed` | 16 / 14 / 15 | 13 / 11 / 12 | 18 / 14 / 16 |
| this harness: `zstd-frame-lane-rule` | 683 / 379 / 788 | 199 / 142 / 390 | 773 / 730 / 1,431 |
| this harness: `zstd-frame-tuned` | 278 / 239 / 529 | 225 / 217 / 414 | 816 / 729 / 1,458 |
| this harness: `zstd-lean-frame-tuned` | 277 / 236 / 528 | 222 / 214 / 417 | 818 / 733 / 1,447 |
| this harness: `zstd-raw-block-tuned` | 258 / 225 / 509 | 210 / 199 / 404 | 807 / 721 / 1,439 |
| this harness: `deflate-raw-lane-rule` | 513 / 310 / 1,679 | 368 / 298 / 671 | 1,555 / 1,709 / 2,243 |
| this harness: `deflate-raw-tuned` | 511 / 324 / 1,667 | 366 / 303 / 685 | 1,749 / 1,813 / 2,378 |
| this harness: `fsst-reference` | 40 / 35 / 58 | 44 / 36 / 66 | 145 / 140 / 207 |
| this harness: `fsst-lane-own-impl` | 5,799 / 5,166 / 10,542 (Python loop) | 6,528 / 5,667 / 12,375 (Python loop) | 29,371 / 27,542 / 44,708 (Python loop) |
| this harness: `zstd-lean-frame-tuned/per-group` | 279 / 257 / 473 | 233 / 215 / 449 | 818 / 753 / 1,211 |
| this harness: `zstd-raw-block-tuned/per-group` | 261 / 239 / 459 | 230 / 204 / 420 | 844 / 784 / 1,281 |
| this harness: `deflate-raw-tuned/per-group` | 546 / 352 / 1,945 | 457 / 347 / 1,690 | 1,880 / 1,852 / 2,504 |
| this harness: `fsst-reference/per-group` | 41 / 33 / 61 | 44 / 34 / 62 | 152 / 140 / 214 |
| this harness: `zstd-lean-frame-blocks-of-2` | 372 / 355 / 641 | 417 / 399 / 670 | 1,607 / 1,516 / 2,282 |
| this harness: `zstd-lean-frame-blocks-of-4` | 919 / 877 / 1,377 | 783 / 729 / 1,117 | 3,406 / 3,417 / 5,259 |
| this harness: `zstd-lean-frame-blocks-of-8` | 1,347 / 997 / 2,307 | 1,433 / 1,406 / 1,922 | 5,916 / 5,558 / 7,492 |
| this harness: `zstd-lean-frame-blocks-of-16` | 2,384 / 1,871 / 4,936 | 3,208 / 2,964 / 4,226 | 9,171 / 9,624 / 10,367 |

## Per suite

### `short_wgsl_vs_json_80_to_80`

Records rebuilt today: train 160 records / 24,121 B, held-out 160 records / 23,924 B. Committed run: train 24,108 B, held-out 23,837 B. **The totals differ: the source files changed after the committed run, so the rebuilt suite is not the same record set.**

Lane, committed (its own run, its own record set):

| codec | held-out bytes | vs BIT3 | ns/seek |
|---|---:|---:|---:|
| BIT3 | 12,092 | +0 | 227 |
| FSST-255 (lane's own implementation) | 14,618 | +2,526 | 50 |
| DEFLATE raw + dictionary | 12,842 | +750 | 513 |
| zstd -19 full frame + dictionary | 14,678 | +2,586 | 194 |

This harness, per-record methods (rebuilt record set):

| method | like-for-like bytes | vs BIT3 committed | all-in | all-in, compact index | model | index | framing | payload | ns/lookup | median ns | p95 ns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| raw-indexed | 24,574 | +12,482 | 24,580 | 24,260 | 0 | 640 | 0 | 23,924 | 16.5 | 14.2 | 15.1 |
| zstd-frame-lane-rule | 14,679 | +2,587 | 14,685 | 14,365 | 2,048 | 640 | 2,080 | 9,901 | 682.8 | 378.9 | 788.0 |
| zstd-frame-tuned | 14,031 | +1,939 | 14,037 | 13,717 | 1,536 | 640 | 2,080 | 9,765 | 278.4 | 239.4 | 528.8 |
| zstd-lean-frame-tuned | 12,751 | +659 | 12,757 | 12,437 | 1,536 | 640 | 800 | 9,765 | 276.9 | 235.8 | 527.8 |
| zstd-raw-block-tuned | 11,971 | -121 | 11,977 | 11,657 | 1,536 | 640 | 20 | 9,765 | 258.1 | 225.4 | 508.8 |
| deflate-raw-lane-rule | 12,865 | +773 | 12,871 | 12,551 | 2,048 | 640 | 0 | 10,167 | 513.5 | 310.1 | 1,678.8 |
| deflate-raw-tuned | 12,316 | +224 | 12,322 | 12,002 | 1,384 | 640 | 0 | 10,282 | 511.3 | 323.9 | 1,667.0 |
| fsst-reference | 14,084 | +1,992 | 14,090 | 13,770 | 671 | 640 | 0 | 12,763 | 39.9 | 34.8 | 58.1 |
| fsst-lane-own-impl | 14,699 | +2,607 | 14,709 | 14,389 | 1,464 | 640 | 0 | 12,589 | 5,799.2 (Python loop) | 5,166.0 | 10,542.0 |
| zstd-lean-frame-tuned/per-group | 12,733 | +641 | 12,783 | 12,463 | 1,024 | 640 | 800 | 10,255 | 279.2 | 256.5 | 473.1 |
| zstd-raw-block-tuned/per-group | 11,953 | -139 | 12,003 | 11,683 | 1,024 | 640 | 20 | 10,255 | 260.8 | 238.9 | 458.9 |
| deflate-raw-tuned/per-group | 12,298 | +206 | 12,348 | 12,028 | 1,500 | 640 | 0 | 10,144 | 546.3 | 351.6 | 1,944.8 |
| fsst-reference/per-group | 13,402 | +1,310 | 13,452 | 13,132 | 1,212 | 640 | 0 | 11,536 | 41.3 | 33.0 | 61.4 |

This harness, small compressed blocks (zstd lean frame per block of N records):

| method | like-for-like bytes | vs BIT3 committed | all-in | model | index | framing | payload | raw bytes decoded per lookup (mean) | ns/lookup | p95 ns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zstd-lean-frame-blocks-of-2 | 11,920 | -172 | 11,926 | 1,024 | 960 | 400 | 9,526 | 299.1 | 371.7 | 640.7 |
| zstd-lean-frame-blocks-of-4 | 10,912 | -1,180 | 10,918 | 1,024 | 800 | 200 | 8,878 | 598.1 | 919.3 | 1,376.9 |
| zstd-lean-frame-blocks-of-8 | 10,082 | -2,010 | 10,088 | 768 | 720 | 100 | 8,484 | 1,196.2 | 1,347.2 | 2,307.4 |
| zstd-lean-frame-blocks-of-16 | 9,584 | -2,508 | 9,590 | 512 | 680 | 50 | 8,332 | 2,392.4 | 2,384.1 | 4,936.2 |

Reproduction check (same rule as the lane, rebuilt record set):

| lane codec | lane committed | this harness, lane rule | difference |
|---|---:|---:|---:|
| zstd -19 full frame + dictionary | 14,678 | 14,679 | +1 |
| DEFLATE raw + dictionary | 12,842 | 12,865 | +23 |
| FSST-255 (lane's own implementation) | 14,618 | 14,699 | +81 |

Framing question:

- Lane, committed: zstd 14,678 B, BIT3 12,092 B, gap +2,586 B.
- Measured framing in the lane-style zstd archive (rebuilt records): 2,080 B (1,600 frame header incl. magic, 480 block header; 13 to 13 B per record).
- Lane zstd committed minus that framing: 12,598 B, which is +506 B against BIT3 committed.
- Smallest per-record baseline here: `zstd-raw-block-tuned/per-group` at 11,953 B, -139 B against BIT3 committed.
- Reference FSST minus the lane's FSST on the same records: -615 B.

### `short_ts_vs_mjs_80_to_80`

Records rebuilt today: train 160 records / 24,607 B, held-out 160 records / 24,245 B. Committed run: train 24,596 B, held-out 24,180 B. **The totals differ: the source files changed after the committed run, so the rebuilt suite is not the same record set.**

Lane, committed (its own run, its own record set):

| codec | held-out bytes | vs BIT3 | ns/seek |
|---|---:|---:|---:|
| BIT3 | 12,390 | +0 | 226 |
| FSST-255 (lane's own implementation) | 14,929 | +2,539 | 53 |
| DEFLATE raw + dictionary | 13,458 | +1,068 | 374 |
| zstd -19 full frame + dictionary | 15,459 | +3,069 | 198 |

This harness, per-record methods (rebuilt record set):

| method | like-for-like bytes | vs BIT3 committed | all-in | all-in, compact index | model | index | framing | payload | ns/lookup | median ns | p95 ns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| raw-indexed | 24,895 | +12,505 | 24,901 | 24,581 | 0 | 640 | 0 | 24,245 | 13.1 | 11.3 | 12.2 |
| zstd-frame-lane-rule | 15,267 | +2,877 | 15,273 | 14,953 | 2,048 | 640 | 2,088 | 10,481 | 199.0 | 142.3 | 389.6 |
| zstd-frame-tuned | 15,155 | +2,765 | 15,161 | 14,841 | 768 | 640 | 2,088 | 11,649 | 224.9 | 217.5 | 413.6 |
| zstd-lean-frame-tuned | 13,867 | +1,477 | 13,873 | 13,553 | 768 | 640 | 800 | 11,649 | 222.2 | 214.4 | 417.3 |
| zstd-raw-block-tuned | 13,087 | +697 | 13,093 | 12,773 | 768 | 640 | 20 | 11,649 | 210.4 | 199.0 | 403.5 |
| deflate-raw-lane-rule | 13,164 | +774 | 13,170 | 12,850 | 2,048 | 640 | 0 | 10,466 | 368.4 | 298.3 | 671.1 |
| deflate-raw-tuned | 12,816 | +426 | 12,822 | 12,502 | 1,894 | 640 | 0 | 10,272 | 365.9 | 303.2 | 685.5 |
| fsst-reference | 14,576 | +2,186 | 14,582 | 14,262 | 652 | 640 | 0 | 13,274 | 44.4 | 35.6 | 66.0 |
| fsst-lane-own-impl | 14,867 | +2,477 | 14,877 | 14,557 | 1,411 | 640 | 0 | 12,810 | 6,527.9 (Python loop) | 5,667.0 | 12,375.0 |
| zstd-lean-frame-tuned/per-group | 13,871 | +1,481 | 13,921 | 13,601 | 1,280 | 640 | 800 | 11,137 | 233.0 | 215.0 | 448.8 |
| zstd-raw-block-tuned/per-group | 13,282 | +892 | 13,332 | 13,012 | 1,024 | 640 | 20 | 11,584 | 230.1 | 204.5 | 420.2 |
| deflate-raw-tuned/per-group | 13,579 | +1,189 | 13,629 | 13,309 | 1,741 | 640 | 0 | 11,184 | 457.3 | 347.4 | 1,689.6 |
| fsst-reference/per-group | 14,490 | +2,100 | 14,540 | 14,220 | 1,275 | 640 | 0 | 12,561 | 44.3 | 34.5 | 61.6 |

This harness, small compressed blocks (zstd lean frame per block of N records):

| method | like-for-like bytes | vs BIT3 committed | all-in | model | index | framing | payload | raw bytes decoded per lookup (mean) | ns/lookup | p95 ns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zstd-lean-frame-blocks-of-2 | 12,704 | +314 | 12,710 | 768 | 960 | 400 | 10,566 | 303.1 | 416.9 | 669.6 |
| zstd-lean-frame-blocks-of-4 | 11,860 | -530 | 11,866 | 768 | 800 | 200 | 10,082 | 606.1 | 782.7 | 1,117.2 |
| zstd-lean-frame-blocks-of-8 | 11,186 | -1,204 | 11,192 | 768 | 720 | 100 | 9,588 | 1,212.2 | 1,433.0 | 1,921.7 |
| zstd-lean-frame-blocks-of-16 | 10,605 | -1,785 | 10,611 | 768 | 680 | 50 | 9,097 | 2,424.5 | 3,208.0 | 4,226.5 |

Reproduction check (same rule as the lane, rebuilt record set):

| lane codec | lane committed | this harness, lane rule | difference |
|---|---:|---:|---:|
| zstd -19 full frame + dictionary | 15,459 | 15,267 | -192 |
| DEFLATE raw + dictionary | 13,458 | 13,164 | -294 |
| FSST-255 (lane's own implementation) | 14,929 | 14,867 | -62 |

Framing question:

- Lane, committed: zstd 15,459 B, BIT3 12,390 B, gap +3,069 B.
- Measured framing in the lane-style zstd archive (rebuilt records): 2,088 B (1,608 frame header incl. magic, 480 block header; 13 to 14 B per record).
- Lane zstd committed minus that framing: 13,371 B, which is +981 B against BIT3 committed.
- Smallest per-record baseline here: `deflate-raw-tuned` at 12,816 B, +426 B against BIT3 committed.
- Reference FSST minus the lane's FSST on the same records: -291 B.

### `med_ts_vs_json_50_to_50`

Records rebuilt today: train 100 records / 58,039 B, held-out 100 records / 60,187 B. Committed run: train 58,293 B, held-out 58,759 B. **The totals differ: the source files changed after the committed run, so the rebuilt suite is not the same record set.**

Lane, committed (its own run, its own record set):

| codec | held-out bytes | vs BIT3 | ns/seek |
|---|---:|---:|---:|
| BIT3 | 30,109 | +0 | 889 |
| FSST-255 (lane's own implementation) | 37,646 | +7,537 | 194 |
| DEFLATE raw + dictionary | 27,664 | -2,445 | 1,387 |
| zstd -19 full frame + dictionary | 27,426 | -2,683 | 750 |

This harness, per-record methods (rebuilt record set):

| method | like-for-like bytes | vs BIT3 committed | all-in | all-in, compact index | model | index | framing | payload | ns/lookup | median ns | p95 ns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| raw-indexed | 60,597 | +30,488 | 60,603 | 60,403 | 0 | 400 | 0 | 60,187 | 17.5 | 13.5 | 15.7 |
| zstd-frame-lane-rule | 27,805 | -2,304 | 27,811 | 27,611 | 2,048 | 400 | 1,400 | 23,947 | 772.9 | 730.5 | 1,431.0 |
| zstd-frame-tuned | 27,519 | -2,590 | 27,525 | 27,325 | 2,048 | 400 | 1,400 | 23,661 | 816.3 | 729.3 | 1,458.0 |
| zstd-lean-frame-tuned | 26,619 | -3,490 | 26,625 | 26,425 | 2,048 | 400 | 500 | 23,661 | 818.2 | 733.0 | 1,446.9 |
| zstd-raw-block-tuned | 26,136 | -3,973 | 26,142 | 25,942 | 2,048 | 400 | 13 | 23,665 | 807.5 | 721.3 | 1,439.4 |
| deflate-raw-lane-rule | 28,064 | -2,045 | 28,070 | 27,870 | 2,048 | 400 | 0 | 25,606 | 1,554.9 | 1,709.5 | 2,242.6 |
| deflate-raw-tuned | 27,884 | -2,225 | 27,890 | 27,690 | 870 | 400 | 0 | 26,604 | 1,748.8 | 1,813.1 | 2,377.6 |
| fsst-reference | 38,474 | +8,365 | 38,480 | 38,280 | 623 | 400 | 0 | 37,441 | 144.8 | 140.1 | 206.7 |
| fsst-lane-own-impl | 38,686 | +8,577 | 38,696 | 38,496 | 1,285 | 400 | 0 | 36,995 | 29,370.8 (Python loop) | 27,542.0 | 44,708.0 |
| zstd-lean-frame-tuned/per-group | 26,555 | -3,554 | 26,605 | 26,405 | 1,280 | 400 | 500 | 24,361 | 818.1 | 753.2 | 1,210.6 |
| zstd-raw-block-tuned/per-group | 26,067 | -4,042 | 26,117 | 25,917 | 1,280 | 400 | 14 | 24,359 | 844.5 | 783.9 | 1,281.3 |
| deflate-raw-tuned/per-group | 27,955 | -2,154 | 28,005 | 27,805 | 983 | 400 | 0 | 26,558 | 1,879.9 | 1,851.7 | 2,504.2 |
| fsst-reference/per-group | 37,371 | +7,262 | 37,421 | 37,221 | 1,276 | 400 | 0 | 35,681 | 152.3 | 139.7 | 213.8 |

This harness, small compressed blocks (zstd lean frame per block of N records):

| method | like-for-like bytes | vs BIT3 committed | all-in | model | index | framing | payload | raw bytes decoded per lookup (mean) | ns/lookup | p95 ns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zstd-lean-frame-blocks-of-2 | 25,939 | -4,170 | 25,945 | 1,024 | 600 | 250 | 24,055 | 1,203.7 | 1,607.3 | 2,281.7 |
| zstd-lean-frame-blocks-of-4 | 25,040 | -5,069 | 25,046 | 1,024 | 500 | 125 | 23,381 | 2,407.5 | 3,406.1 | 5,259.5 |
| zstd-lean-frame-blocks-of-8 | 24,062 | -6,047 | 24,068 | 1,024 | 452 | 65 | 22,511 | 4,696.2 | 5,916.3 | 7,492.1 |
| zstd-lean-frame-blocks-of-16 | 22,492 | -7,617 | 22,498 | 0 | 428 | 35 | 22,019 | 9,273.8 | 9,170.6 | 10,367.4 |

Reproduction check (same rule as the lane, rebuilt record set):

| lane codec | lane committed | this harness, lane rule | difference |
|---|---:|---:|---:|
| zstd -19 full frame + dictionary | 27,426 | 27,805 | +379 |
| DEFLATE raw + dictionary | 27,664 | 28,064 | +400 |
| FSST-255 (lane's own implementation) | 37,646 | 38,686 | +1,040 |

Framing question:

- Lane, committed: zstd 27,426 B, BIT3 30,109 B, gap -2,683 B.
- Measured framing in the lane-style zstd archive (rebuilt records): 1,400 B (1,100 frame header incl. magic, 300 block header; 14 to 14 B per record).
- Lane zstd committed minus that framing: 26,026 B, which is -4,083 B against BIT3 committed.
- Smallest per-record baseline here: `zstd-raw-block-tuned/per-group` at 26,067 B, -4,042 B against BIT3 committed.
- Reference FSST minus the lane's FSST on the same records: -212 B.

