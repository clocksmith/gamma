# WIKIFORWARD Prior-Destination Lexicon QM1

Proposal ID: `wikiforward_prior_destination_page_lexicon_qm1_v1`

Status: dormant zero-credit ceiling. Do not implement or queue this proposal
until WIKIBACK and then WIKISECTION reach terminal dispositions.

## Question

Does a completely decoded outgoing link to an earlier closed page expose a
page-specific lexical source for later text in the current page that remains
absent from the JANUS-plus-quotient trajectory and from the current-page
prefix?

This is the graph direction opposite WIKIBACK. WIKIBACK uses completed prior
incoming-link neighborhoods to predict a later target page. WIKIFORWARD uses a
completed current outgoing-link target to retrieve the already closed
destination article and predict only later events in the current page.

The gate is a deliberately free truth-aware ceiling. It is not a codec result
and receives zero forecast credit.

## Frozen population and parent

Use the canonical opening-10M inputs and exact WRT/page/link grammar:

- the exported JANUS-plus-quotient adjusted P1 trajectory;
- its matching truth and WRT streams;
- exact complete-page boundaries and title/link parsing;
- the official WRT-to-raw inverse receipt;
- chronological complete-page splits of 60%, 20%, and 20%;
- the trailing partial page is parsed for integrity but contributes no active
  WIKIFORWARD opportunity.

All rounded loss is measured in Q256 bits. One byte-equivalent is exactly
`2048` Q256 units.

Bind exact size and SHA-256 for the joint P1 and `1,617,484`-byte parent
payload, matching WRT store, raw 10M, dictionary, official inverse, and exact
page map before parsing. Bind
`tools/mobius2_tessera_typed_fiber_ceiling.py::qbit_tables`: `float64`
`-log2(p) * 256`, `numpy.rint` nearest-even, and canonical little-endian
`int32` tables. The zero/one table SHA-256 values are
`6ddbe07c8c2f8387d044a98d958e26ac4f8af27a9dcdf2335f046891365c2376`
and `7caf35600227bad3b1b7402aaa3837aab1aa5aa11267bca283be055c81e8387f`.

Frozen artifact identities:

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

Freeze the direct donor semantics as well. A read-only preflight on 2026-08-02
reproduced these tracked Git blobs and content hashes:

```text
donor                                                     Git blob                                  SHA-256
tools/wikiback_incoming_anchor_context_qh0.py             0e6d653f69d94aeaf4f149ab8982aeade929e92c  5a6bb8f47e7250f5eac16a5803c0fadbc032f70aa0a06cd1fb4e5e1f140c9638
tools/causal_state_screen.py                              18c55e347e69860529a76cb6e5069ac597685dd7  aaa42365acadc8e32f8b79e5862ca451a91d637093b483bcf54cbf657c4740e4
tools/mobius2_tessera_self_annotation_graph.py            2f066cd73ab054d5b4a8902aa2018348b9fe00cb  0d5168f834c24153657ba162e2bfab3f6cce9fd1396e1079e8e8ac7c09318594
tools/mobius2_tessera_typed_fiber_ceiling.py              b7d8e80b051b98362d36984719ddbd8be24fd8d4  c1e404b9f5328df6f75ae3ffef6e4c9bb9d3757c31c54905ae727c1b68578af3
tools/sibyl_page_prompt_oracle.py                         e2104295ba54b9725d58b1c0d9d9285ae5eca236  68b209861d3d46113acff2d3313a58237e01c620d331d11ccec3c846b99d00d6
tools/wrt_exact.py                                        5285841cd9107b915b31be5b94ab54ac0a8040c7  ae08246ee8b4708904f78aa5f694111834d6420deece34957c61d6fea3a9797a
```

Materialization must use these exact donor bytes or create a new proposal
version with an explicit mechanism/source change. Merely importing whatever
functions happen to be at a later HEAD would not reproduce this frozen gate.

## Causal contract

For every complete page, stage a lexicon containing only lexical WRT events
already decoded in that page. Parse links across the complete `<page>` using
the current WIKIBACK grammar, not only Wiki `field_id == 6`.

The donor `PageStage.links` is published only at final `]]`, which is too late
to score a link label. Materialization must add an explicit `target_complete`
signal. It fires immediately after the first decoded event-aligned `|`, `#`, or
`]]` that ends the target, before the next WRT event. No event containing that
terminator is itself an opportunity. A later malformed label or closer does
not retroactively revoke already exposed later opportunities.

At `target_complete`, normalize the exact decoded target with WIKIBACK's ASCII
normalization. Resolve it against the title index as it exists at that instant.
If exactly one strictly earlier fully closed page ordinal exists, add that
immutable page lexicon to the current page's active destination set. Later
duplicate titles cannot retroactively disable the resolved source. Empty keys,
unresolved or duplicate keys, and empty prose lexicons perform no update.

Only later `LINK_LABEL` and `PROSE_WORD` events may be scored. Event role is
`tools/mobius2_tessera_self_annotation_graph.py::role_id(WikiState)` evaluated
before truth. Candidate identity is the raw `WrtEvent.encoded` bytes, and its
loss rows are `[8 * event.start, 8 * event.end)`. Truth-aware eligibility also
requires `event.kind == "token"`, checked only after reveal. Score first, then
update the Wiki/parser state and current-page prefix. At the prediction
boundary, event truth, eventual length, and future page bytes are invisible.
The optimistic membership decision is evaluated after truth solely for the
free ceiling. A qualifying hit must be absent from the exact already decoded
current-page prefix lexicon.

Resolve targets with exactly the frozen WIKIBACK ASCII normalization and no
additional Unicode, entity, redirect, semantic, or alias normalization. A
source page must have a strictly smaller completed-page ordinal. The title
index maps normalized key to ordered fully closed page records; a non-unique
key performs no update.

A destination lexicon is `Counter[WrtEvent.encoded]` over exact token events
whose pre-event role is `PROSE_WORD`. Commit its normalized title key and
counter atomically only after `</page>`; never commit the trailing partial
page. The current page's active source is an idempotent set of destination page
ordinals: repeated links to the same destination do not add its counts again,
while counters from distinct active pages sum once. Current-page prefix novelty
is defined over every previously completed exact token identity in every role;
an identity previously seen in markup, a heading, link syntax, or another role
is therefore not novel. Prefix state resets at page open.

## Frozen exploratory observation

A read-only exact-trace audit found 1,528 causally resolvable links across 581
active pages. The unrestricted destination lexicon displaced
`212,729.165` byte-equivalent, but a generic current-page prefix lexicon
displaced `214,966.411`; unrestricted gain is therefore not specific.

Restricting to exact destination hits absent from the decoded current-page
prefix exposed `63,259.358` byte-equivalent:

| Split | Byte-equivalent | B/M |
|---|---:|---:|
| Development | 36,810.787 | 5,732 |
| Selection | 13,539.301 | 7,373 |
| Confirmation | 12,909.270 | 7,448 |

These numbers are hypothesis evidence only. They were not produced by a paid
side stream, reconstruction archive, or decoder and receive zero score credit.
The exploratory command, source, and output were not retained in the
repository or the nonproof artifact archive. A Git-history and filesystem
search on 2026-08-02 found the values only in this plan and the research
register. They are therefore unverified narrative observations, not an exact
receipt or an independently reproducible ceiling. QM1 must rebuild the parser,
causal index, opportunities, Q256 totals, and all splits from the bound inputs;
it may not import these values as expected outputs or use them to satisfy any
gate.

## Exact QM1 lanes

All lanes must receive the same causally visible resolved-target updates. They
must expose identical opportunity positions and identical cumulative unique
lexeme count and weight multisets before truth is examined.

- `Dfull`: lexicons of the exact earlier destination pages named by completed
  current-page outgoing links.
- `Dblind`: at each target update, exclude the real destination key and every
  blind source ordinal already active in the current page. Among earlier closed
  pages with enough unique prose identities, minimize absolute
  `unique_count.bit_length()` distance to the real destination, then choose by
  ascending page ordinal and normalized title key. Store and digest both.
- `Dprior`: the immediately previous fully closed page's prose reservoir.
- `Dglobal`: exact token counts accumulated from all prior closed-page prose
  lexicons. Global counts update atomically at page close.

A destination update is accepted atomically for every lane only if all three
per-update source reservoirs exist. A failed update is discarded without
removing earlier accepted sources.

At every opportunity, prefix-filter each cumulative reservoir. Let `U` be the
number of unique `Dfull` identities remaining and sort `Dfull` weights
descending. Select each control's `U` identities by descending causal source
count then ascending raw encoded bytes, and assign the sorted `Dfull` weight
multiset in that order. A match made at an earlier destination update is not
sufficient because later prefix events remove different identities. If any
control has fewer than `U` identities, deactivate only the current opportunity
for every lane. No lane may receive an extra opportunity.

The following repeated-build digests must be byte-identical:

- exact parser events and page/title/link boundaries;
- target-completion activations and duplicate-title point-in-time resolutions;
- page lexicons and active destination ordinals;
- prior-page title index and destination resolutions;
- opportunity positions and prefix-novel masks;
- per-update control assignments and capacity multisets;
- per-lane rounded-Q256 totals and split totals.
- exact joint-parent payload bytes and SHA-256;
- exact decoded WRT bytes and official raw inverse SHA-256.
- canonical Q256 table bytes and SHA-256.

## Free and paid boundary

QM1 temporarily supplies the destination index, lexicons, counts, ranks,
membership selector, source, framing, and termination for free. It sums only
the exact rounded-Q256 joint-parent loss of prefix-novel truth events present
in each lane's exposed lexicon. No projected source or archive saving is
claimed.

Any successor Q0 must encode an actual hit/escape decision, exact rank or
lexeme identity, surface realization, residual bits, framing, termination, and
source package, and must reconstruct WRT and raw bytes exactly.

## Decision rule

Authorize only a separately materialized paid Q0 when all conditions hold:

```text
all sources strictly earlier and completely closed       pass
parser/index/opportunity/control repeated digests         exact
lane opportunity and capacity multisets                   identical
Dfull total                                               >= 60,000 byte-equivalent
Dfull development                                         >= 5,000 B/M
Dfull selection                                           >= 5,000 B/M
Dfull confirmation                                        >= 5,000 B/M
Dfull minus each control, total                            >= 10,000 byte-equivalent
Dfull minus each control, every split                      positive
```

For a split containing `R` raw bytes, compare the integer quantities directly:

```text
split_qbits * 1,000,000 >= 5,000 * 2,048 * R
```

Do not use rounded floating-point B/M values in the decision.
`R` is the sum of exact page-map raw spans for complete pages in that
page-count split. Carry parser, title, lexicon, and current causal state across
split boundaries; independently reported split totals do not reset state.

Any miss retires this exact destination-source union, prefix-novel filter,
event universe, and control construction. Do not rescue-sweep link windows,
target normalization, redirects, lexicon roles, support, weighting, capacity,
or control selection.

A pass authorizes only an isolated actual paid hit/escape-plus-rank Q0 for
attribution. It does not authorize native integration, a larger population,
source-bound forecast credit, or a full-corpus claim. If WIKIBACK or
WIKISECTION also pays, isolated gains must not be added; the only score-relevant
evidence is a fresh joint finite replay with frozen precedence and all source
and framing costs.

## Ordering

1. Let the active NNCP gate reach a terminal receipt.
2. Queue and execute the corrected, source-bound WIKIBACK v2 gate exactly once.
3. Apply WIKIBACK's frozen decision mechanically.
4. Resolve the dormant WIKISECTION QM1 before this proposal.
5. Only then claim, implement, source-bind, and queue WIKIFORWARD QM1.

The first materialization must bind the plan, candidate tool, and direct donor
sources to HEAD and build parser/index/control/Q256 state twice independently.
Receipt digests must cover target activations, duplicate resolutions, page
lexicons, active-source ordinals, prefix masks, opportunities, candidate lists,
and per-lane split totals. The proposal's `196,608`-byte ceiling applies to a
later paid Q0; QM1 supplies source and model free and earns zero score credit.
The first QM1 decision must explicitly state whether it reproduces or
contradicts the unretained exploratory observation; only QM1's own artifact-
bound integer totals may be cited afterward.
