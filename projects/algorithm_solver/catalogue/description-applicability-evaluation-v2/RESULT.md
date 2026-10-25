# Cached guard-v2 development result

The main-reviewed freeze `63cc9a9a7adecab59bbc22611f1d834e484a2f640403a7873232b1a926a1558f`
completed on DOT within the authorized 512 MiB / 60 CPU-second / 60 wall-second
budget. Private report:
`/workspace/shared/gamma-description-applicability-eval-v2-20261025-2137/report.json`,
SHA256 `70810d13061dcf6d49fafb8892834f59991b62065c53778d703ba67b75ed83c9`.

**Negative result: no applicability improvement.**

- All 20 historical baseline decisions/metrics reproduced over all 4,081 competitors.
- Guard v2 extracted zero facts on all 52 unrestricted descriptions; zero complete
  grammar parses. Every policy's metrics are unchanged.
- Selected `c65-m12`: 9/40 correct positive accepts, zero wrong positive accepts,
  zero of 12 control accepts, 43/52 abstentions.
- Loose `c45-m00`: still 34/40 correct positive accepts and 9/12 control accepts.
- Runtime: 6.139 seconds wall, 6.127 seconds CPU, 127,436 KiB peak RSS.
- No encoder invocation, candidate source read/execution or confirmation access.

The narrow grammar has useful synthetic correctness controls but **no extraction
coverage on this authored cohort**. It does not resolve goal 1b. Grammar and
thresholds were not changed after observing this result. Recognition remains
unqualified; this non-IID development comparison is not independent confirmation,
a risk certificate, or a measurement of fresh-query serving latency.
