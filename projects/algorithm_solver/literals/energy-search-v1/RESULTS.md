# Portable synthetic mechanism result

The final reviewed revision passes **30/30 tests**, the same **18 arms** and **32-state reference**. Independent review identified and repaired contract, direct-API and alias-boundary gaps before commit. All arm cost records, rejections and winner identities below remain unchanged; this is stronger eligibility enforcement, not a new compression result. [Repair receipt](receipts/review-repairs-v2.json) and [current test log](receipts/review-tests.txt) preserve the details and failed development attempts.

## Initial adapter evidence (preserved)

The portable checkout adapter passed **24/24 focused tests**, **18 designed/mined/combined seed arms**, and the **32-state exact reference** on 2026-10-21 at 22:58:04 UTC. CPU13 usage was 0.160 CPU seconds, with 28,524,544 bytes peak RSS, within the 512 MiB / 20 CPU-second bounds.

All 43 files from the original private frozen run remain byte-for-byte unchanged. All 18 candidate manifests, exact cost records, rejection records and winning state identities match that run. The synthetic dataset and tiny-reference bytes also match. Code changes are limited to dependency paths, the portable seed fixture/provenance-test adapter, and relative dependency receipt paths; [PORTABILITY.md](PORTABILITY.md) describes the narrowed provenance check.

| Seed policy / track | Coverage | Selections | 6-bit package bits | 7-bit package bits | 8-bit package bits |
|---|---:|---:|---:|---:|---:|
| Designed-only, either track | 0/2 | unavailable | unavailable | unavailable | unavailable |
| Mined-only, compression | 2/2 | 598 | 6,024 | 6,624 | 7,208 |
| Combined, compression | 2/2 | 174 | 5,320 | 5,488 | 5,656 |
| Mined-only, readable lines | 2/2 | 26 | 5,088 | 5,120 | 5,136 |
| Combined, readable lines | 2/2 | 26 | 5,088 | 5,120 | 5,136 |

These are two synthetic strings, not qualified problem solutions. Package bits include dictionary storage and padded packets, including 41-byte framing per program. Decoder storage is separately recorded. The designed-only three-seed dictionary cannot encode full function/loop/return text; it receives zero coverage and null best/cost rather than a free alphabet. Readable line entries may be partial blocks, and memorability is unmeasured.

The tiny reference exhausts only three candidate additions and two source alternatives for each of two programs. Its fixed-source greedy gap and additional source-choice opportunity are both zero. This finite result does not establish a global optimum or an advantage for an energy model.

**Zero model training, zero candidate-source execution, zero real problem qualification and no publication occurred.** Learned scoring is an interface exercised with constant test spies. A trainable pairwise-logistic model remains proposed in [PROTOCOL.md](PROTOCOL.md). Track B description-to-assembly and independent generalization remain unimplemented.

The [aggregate receipt](receipts/portable-smoke-v1.json), SHA256 `40a91996adb8323559003e3cb3d9b62dba57b8e089ac9e0d9fe3ce834cc8add3`, records bounds, source/code/dependency identities, all arm metrics and exact portability parity. The [test log](receipts/tests.txt) lists all 24 checks. The detailed synthetic run is reproducible locally with the README command; original private source and test bodies are not part of this package.
