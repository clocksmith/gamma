# WIKISECTION exact-heading body-lexicon QM1 plan

Candidate: `wikisection_exact_heading_body_lexicon_qm1_v1`

Status: proposed and dormant until the WIKIBACK QH0 decision

Evidence level: zero-credit causal candidate universe with a truth-aware oracle
selector

## Question

Test whether an exact completed section heading identifies lexical information
in prior completed sections with the same heading that remains absent from the
exact JANUS-plus-quotient trajectory. This is a different source from the
retired ten-state heading residual calibrator: the exact heading bytes become a
causal key into chronological section-body memory, and QM1 measures whole exact
WRT token events rather than adjusting bit logits.

## Frozen population and grammar

Use canonical opening 10M with the receipt-bound JANUS-plus-quotient P1, WRT
truth/store, raw input, exact page map, dictionary, and official inverse. Carry
state through all complete pages and report first 60%, next 20%, and final 20%
of complete pages as opened development, selection, and confirmation
diagnostics.

Bind those inputs before parsing. A read-only preflight on 2026-08-02
reproduced every byte count and SHA-256 below:

```text
joint P1       results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1
bytes/SHA      100,029,648  b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719
parent payload results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload
bytes/SHA      1,617,484  5ffaa128fa9e86e3883896a6d16b6c49e23693f5abdf14f1718e0e006533dca9
WRT store      results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin
bytes/SHA      6,251,857  867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b
raw 10M        /home/x/enwiki9-nonproof/gamma/projects/enwiki9/data/enwik9_10000000.bin
bytes/SHA      10,000,000  5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97
dictionary     /home/x/enwiki9-nonproof/results/cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/clean-build-b/build/english.dic
bytes/SHA      411,996  4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a
page receipt   results/sibyl_page_boundaries_v1/receipt.json
bytes/SHA      9,711,214  e4f0db7f82759aa05b025cd65170206cb76fd22187eb29d7bbe96537928c7bcc
inverse backend SHA-256
               d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194
```

QM1 must reproduce the joint parent payload before reporting a ceiling and
must bind its derived page intervals back to the page receipt. A missing or
different artifact is malformed input, not a scientific rejection.

The byte parser is active only after the exact case-sensitive decoded opener
`<text xml:space="preserve">` and before the exact case-sensitive closer
`</text>`, exactly as recognized by the bound `WikiState`. The first byte after
the opener's closing `>` and every byte after LF (`0x0a`) begins a line. Buffer
one whole decoded line through LF before classifying it; EOF without LF is not
a heading. Remove the terminal LF and then one terminal CR, if present. Do not
allow leading space or tab before an opening run. Let `w` be the maximal leading
run of `=`. Strip trailing ASCII space/tab, let `v` be the maximal trailing run
of `=`, and accept the line only when `2 <= w <= 6`, `v == w`, and the bytes
between those runs are nonempty after ASCII space/tab trimming. An extra or
mismatched outer `=` run is therefore rejected. Internal `=` bytes are ordinary
heading content. Headings are non-nested and any bytes after the balanced close
other than ASCII space/tab make the line non-heading.

Normalize the accepted heading body by trimming and collapsing exactly the
ASCII byte set `{0x09,0x0a,0x0b,0x0c,0x0d,0x20}`, ASCII-lowercasing bytes
`A` through `Z`, and converting underscore to space. Do not apply Unicode
normalization, entity expansion, semantic labels, page labels, or a global
corpus index.

A section body begins with the first event after the completed heading newline
and ends before the first event contributing bytes to the next accepted heading
line or the completed exact `</text>` closer. Keep every decoded line's WRT
events pending until LF or text close: if it
is an accepted heading, exclude the entire line from both neighboring bodies;
otherwise append its wholly contained dictionary-token events to the current
body. Exclude any WRT event whose decoded bytes cross a text, page, line, or
heading/body boundary. Publish section records only after the enclosing page
closes, so neither the current section nor any later content from its page can
train its own snapshot. Canonical 10M has 1,325 closed pages and a trailing
partial page; exclude that partial page from QM1 economics, never publish its
staged records, and require an eventual Q0 to transmit the complete-page limit
and code the tail only through the parent residual.

Bind text-field visibility to `tools/causal_state_screen.py::WikiState.field_id
== 6`, Git blob `18c55e347e69860529a76cb6e5069ac597685dd7`, SHA-256
`aaa42365acadc8e32f8b79e5862ca451a91d637093b483bcf54cbf657c4740e4`.
Bind `PROSE_WORD` to
`tools/mobius2_tessera_self_annotation_graph.py::role_id`, Git blob
`2f066cd73ab054d5b4a8902aa2018348b9fe00cb`, SHA-256
`0d5168f834c24153657ba162e2bfab3f6cce9fd1396e1079e8e8ac7c09318594`.

At heading completion, snapshot all records from earlier completed pages under
the exact normalized heading. Declare opportunities before each later
decoder-visible `PROSE_WORD` event using only that snapshot and completed state.
After the event is revealed, a free truth-aware oracle attributes a hit only
when the event is an exact encoded WRT dictionary token present in the
snapshot. Current event kind, truth, and length are unavailable to the
opportunity schedule but are deliberately free to the QM1 membership selector.
This makes QM1 an optimistic information ceiling, not a causal codec or an
occurrence-level score claim.

Opportunity scheduling uses the pre-event `WikiState`. A buffered line may not
retroactively delete opportunities merely because the completed line is later
recognized as a heading. Instead, an accepted heading line must contain zero
scheduled dictionary-token opportunities; any violation makes the execution
causally malformed. When `</text>` is reached without a preceding LF, finalize
the preceding body line as non-heading while excluding every event that
contributes any byte to the closer. Exclude every event crossing a closer or
line boundary.

## QM1 controls

QM1 supplies the index, counts, truth-aware selector, ranks, source, framing,
and stream termination for free. For each oracle hit, sum the integer rounded
Q256 codelength of its exact JANUS-plus-quotient truth bits. Report only
`Q256-byte-equivalent = qbits / 2048`; do not call it an archive or finite-coder
saving. All decisions compare integer qbits directly to
`threshold_bytes * 2048`. It is not a codec result.
For a chronological split with `R` raw bytes in the complete-page XML spans
reported by the exact page map, compare
`split_qbits * 1,000,000` directly with `5,000 * 2048 * R`; do not round a
floating-point B/M value to make the decision.

Freeze Q256 construction to
`tools/mobius2_tessera_typed_fiber_ceiling.py::qbit_tables`. It evaluates
`-log2(p) * 256` in `float64`, uses `numpy.rint` nearest-even rounding, and
stores native results as `int32`. Canonical receipt serialization is 65,536
little-endian signed 32-bit entries in probability-index order:

```text
zero-bit table bytes   262,144
zero-bit table SHA-256 6ddbe07c8c2f8387d044a98d958e26ac4f8af27a9dcdf2335f046891365c2376
one-bit table bytes    262,144
one-bit table SHA-256  7caf35600227bad3b1b7402aaa3837aab1aa5aa11267bca283be055c81e8387f
```

Rebuild both tables independently and require these hashes before scoring.
The tables are supplied free in QM1 but remain bound evidence; a later finite
Q0 must account for its actual coder rather than these diagnostic Q256 tables.

All lanes use identical pre-truth opportunities and injective capacity
matching. For exact snapshot unique count `U`, each control must expose exactly
`U` distinct encoded token identities. Select identities by descending source
frequency then ascending encoded bytes; source page and section ties use
ascending chronological ordinals. Counts and weights are free and do not affect
QM1 membership scoring. If any control cannot supply `U` identities from
completed prior state, deactivate that section for every lane.

```text
Hblind  one earlier section whose normalized heading differs from the current
        key, selected among sources with at least U identities by minimum
        `abs(source_unique_count.bit_length() - U.bit_length())`, then page
        ordinal, section ordinal, and normalized heading bytes
Hprior  all wholly contained body tokens from the immediately previous
        completed page, truncated to U by the canonical identity order. Body
        tokens means only tokens assigned to sections begun by an accepted
        heading; lead text before the first accepted heading is excluded.
Hcoarse the union of prior completed section bodies with the same frozen coarse
        class but a normalized heading unequal to the current exact key,
        duplicate counts summed and identities truncated to U canonically
Hexact  prior completed bodies under the exact normalized heading
```

Every stored `Hblind` record retains its page ordinal, section ordinal, and
normalized heading key. The selector must explicitly assert that its source
heading key differs from the current exact key; a digest match without this
identity guard is malformed evidence.

`Hcoarse` is bound to `tools/build_heading_state_map.py::classify`, Git blob
`d32fc719bf235aa9e9257518da2e738e3350c0b4`, SHA-256
`91074cdb2c0eb9e9c67c486e34e5bef6efb260517411fe90d77cf43ee581666c`.
Pass the complete accepted raw heading line, including delimiters and terminal
LF, to that function. Its ten returned integer states are used unchanged.

## Frozen decision

Require all of:

```text
parent input identities                         exact
parser/index replay                             byte-identical
opportunity and control digests                 byte-identical
all candidates sourced from prior closed pages exact
Q256 table hashes                               exact
accepted heading has zero scheduled token events exact
closer and line-crossing events excluded             exact
Hblind source-key inequality                         exact

Hexact full free displaced ceiling              >= 60,000 byte-equivalent
Hexact each chronological split                 >= 5,000 B/M
Hexact - max(Hblind,Hprior,Hcoarse), full        >= 10,000 byte-equivalent
Hexact control margin on every split            positive
```

Apply three dispositions. If `full_qbits < 30,000 * 2048`, this is a valid
`REJECT` that retires this exact heading grammar, normalization, section-body
event universe, page-close commit policy, and matched controls. If
`30,000 * 2048 <= full_qbits < 60,000 * 2048`, or if `full_qbits` clears the
upper bound but any attribution/split gate misses, `PARK` the family without Q0
because it misses the intentional two-times portfolio authorization margin but
is not information-theoretically closed. If `full_qbits >= 60,000 * 2048` and
every split and attribution gate passes, `AUTHORIZE_Q0`. Do not sweep heading
width, support, normalization, section windows, or coarse classes after any
disposition.

A pass authorizes only one Q0 with an actual finite Q24 per-section KT
hit/escape stream, frozen hit-rank stream, distinct residual arithmetic
payloads, decoder-built opportunity schedule, exact WRT/raw inverse, repeated
archive identity, at least 30,000 gross bytes, positive opened splits, at least
2,100 B/M after measured compressed source, and
`T(Hexact) < T(Hblind), T(Hprior), T(Hcoarse)` for the paid totals.
Q0 remains zero-credit.

If WIKIBACK rejects, Q0 compares against the exact joint parent. If WIKIBACK
passes, the primary Q0 must be a joint WIKIBACK plus WIKISECTION replay with one
frozen precedence rule and both side costs, measuring only incremental events
not already bypassed. Separate gains and forecasts must never be added.
