# Competitive evidence refresh, 2026-09-16 UTC

The [official page](https://www.hutter1.net/prize/) still displays an awarded
record of **110,793,128 bytes**. The derived one-percent ceiling is
109,685,196 bytes, subject to the committee's applicable reference and accounting.

[Mahoney's benchmark](https://mattmahoney.net/dc/text.html#0960) now lists
James Byrne's zmix submission and says committee testing is underway:

| Published component | Bytes |
| --- | ---: |
| Self-extracting archive | 96,096,261 |
| Compressor | 3,216,163 |
| Sum | **99,312,424** |

The reproduced author description attributes changes to retraining with a
weight-description cost, tighter weight storage, a Zig model-stack port, and
mixer/context-model changes. These are a combined submission, not individual
ablation results. The entry's own README and writeup were not retrieved: the
direct requests returned HTTP 403. No model or executable was downloaded.

The [RATA author README](https://github.com/Dharmesh2015/RATA-CMIX) reports
100,219,121 combined bytes, but explicitly says decompression has not yet run
and its decode timing is estimated. It describes a compact correction after
SSE trained on its own error. Therefore final-coder correction is already
public precedent; Gamma must distinguish its actual contribution. Neither the
README nor this review establishes an accepted Hutter award.

## Exact arithmetic and implications

If 99,312,424 becomes the accepted reference under unchanged one-percent rules,
the integer ceiling would be:

```
floor(99,312,424 * 99 / 100) = 98,319,299 bytes
```

The historical 99M objective would not clear that conditional ceiling. The
active **90,000,000-byte** objective remains unchanged. The difference from the
published zmix sum is 9,312,424 bytes; that is an external comparison, not a
Gamma deficit measured on Gamma's codec. The corrected FX2 sum of 100,420,830
exceeds the zmix sum by 1,108,406 bytes. No individual change may inherit that
difference.

The research consequence is to keep complete program/model/data cost in the
objective, and to test each proposed correction against the final arithmetic
stream. A larger list of specialists or a language port alone is not an
identified cause of the published advantage. The fixed value-feedback gate
already provides a matched native comparison; this refresh does not change its
features, controls, population, admission, or thresholds. The active 10MB trim
comparison also remains untouched.

The [canonical frontier](../operations/provenance/competitive_frontier_v1.json)
now contains the new dated evidence, with its previous contents preserved
[exactly](../operations/provenance/competitive_frontier_before_20260916.json).
[The receipt](../operations/provenance/competitive_frontier_refresh_20260916.json)
binds retrieved source bytes and records retrieval failures. Gamma's verified
full1G score remains unknown; external reports earn no Gamma score credit.
