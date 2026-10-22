# Joint80 8-bit v2 guide package

Promotion package for BITS slot "JavaScript 80, literal, 8-bit" under
[BITS_PROMOTION.md](../BITS_PROMOTION.md). It packages the `ils-256-s2` result of
[matched80-v3](../matched80-v3/README.md) (frozen `a24b8c0f3`, results `4773b2d0b`) as
`bits-literal-joint80-8-v2`, superseding `bits-literal-joint80-8-v1`.

| Profile | Entries / bits | Selections | Median / p95 | Package bytes |
| --- | --- | ---: | --- | ---: |
| `bits-literal-joint80-8-v1` (live) | 256 / 8 | 6,413 | 63 / 168 | 11,781 |
| `bits-literal-joint80-8-v2` | 256 / 8 | **6,161** (-3.93%) | 60 / 167 | **11,750** (-0.26%) |

The bar was at most 6,284 selections and 12,370 package bytes. All five frozen seeds of
the experiment clear it (6,161-6,171), so the candidate is not a lucky seed. Package
bytes count the LTD1 dictionary (2,309 B) and every LTV1 packet with its 41-byte header
(9,441 B). UI controls, navigation and the shared decoder are not included. Against the
live profile, 55 problems need fewer selections, 11 the same and 14 more; the largest
increase is +20 on #1046.

All 80 sources are the compact sources already published in the live 8-bit guides
(same SHA-256 per problem, listed in
[published-8-v1-sources.json](published-8-v1-sources.json), exported from BITS
`bits-literal-joint80-8-v1`). Each has passing verdicts in both the stored and the
re-run scale-v2 qualification receipts. No new source is distributed and none was
executed.

`python3 build.py published-8-v1-sources.json` wrote [package.json](package.json) and
[dictionary.ltd](dictionary.ltd) from the experiment output; it refuses to overwrite.
`python3 verify.py` (byte-identical to the
[7-bit v2 verifier](../guides-joint80-v2/verify.py)) independently rebuilds every
packet and decodes it through the canonical codec. It checks each sequence is a minimum
parse with its own forward shortest-path oracle, checks both receipts and the
published-source match, reconciles totals and writes
[verification.json](verification.json): 80 of 80 programs verified, 6,161 selections,
11,750 package bytes.

These are offline encodings of the same 80 qualified programs: an improved
representation, not broader problem coverage, autonomous synthesis, human fluency,
unseen generalization or M1 qualification.
