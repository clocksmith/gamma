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
