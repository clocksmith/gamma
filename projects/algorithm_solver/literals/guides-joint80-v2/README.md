# Joint80 7-bit v2 guide package

Promotion package for BITS slot "JavaScript 80, literal, 7-bit" under
[BITS_PROMOTION.md](../BITS_PROMOTION.md). It packages the `polish-128` result of
[matched80-v2](../matched80-v2/README.md) (frozen `e1152485e`, results `4d29bfb4a`) as
`bits-literal-joint80-7-v2`, superseding `bits-literal-joint80-7-v1`.

| Profile | Entries / bits | Selections | Median / p95 | Package bytes |
| --- | --- | ---: | --- | ---: |
| `bits-literal-joint80-7-v1` (live) | 128 / 7 | 10,155 | 107.5 / 285 | 13,002 |
| `bits-literal-joint80-7-v2` | 128 / 7 | **9,910** (-2.41%) | 106 / 267 | **12,798** (-1.57%) |

Package bytes count the LTD1 dictionary and every LTV1 packet with its 41-byte header;
UI controls, navigation and the shared decoder are not included.

All 80 sources are the compact sources already published in the v1 guides (same
SHA-256 per problem), each with passing verdicts in both the stored and the re-run
scale-v2 qualification receipts. No new source is distributed and none was executed.

`python3 build.py <v1-guides.json>` wrote [package.json](package.json) and
[dictionary.ltd](dictionary.ltd) from the experiment output; it refuses to overwrite.
`python3 verify.py` independently rebuilds every packet, decodes it through the
canonical codec, checks each sequence is a minimum parse with its own forward
shortest-path oracle, checks both receipts and the published-source match, reconciles
totals and writes [verification.json](verification.json).

These are offline encodings of supplied programs: not autonomous synthesis, human
fluency, unseen generalization or M1 qualification.
