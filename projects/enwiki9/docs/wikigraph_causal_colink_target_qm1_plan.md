# WIKIGRAPH Causal Co-Link Target QM1

Proposal ID: `wikigraph_causal_colink_target_qm1_v1`

Status: dormant zero-credit candidate-universe ceiling. It follows WIKIBACK,
WIKISECTION, and WIKIFORWARD. Do not implement or queue it while those higher
priority representation gates remain unresolved.

## New information source

Before any byte of a current `[[target...]]` has been decoded, predict the
exact target WRT program from relation composition in a graph built only from
fully closed earlier pages.

The frozen composition is:

```text
current page title
<- earlier closed page that linked to this title
-> another exact target linked by that earlier page
```

This differs from WIKIBACK, which transfers lexical neighborhoods around prior
incoming anchors into prose, and WIKIFORWARD, which waits for the current
target to finish before retrieving the earlier destination page's prose
lexicon. The bypass, hit/escape notation, title/link parser, and decoder-built
storage are inherited ideas; the new question is whether prefix-built graph
topology predicts the next exact link-target identity.

## Population and parent

Use the exact JANUS-plus-quotient opening-10M trajectory, exact WRT truth and
page map, the 1,325 complete pages, chronological complete-page 60/20/20
splits, and the exact link grammar bound by
`docs/wikiback_incoming_anchor_context_qh0_plan.md`. The trailing partial page
is residual-only and supplies no graph state.

Loss is summed in rounded Q256 bits; one byte-equivalent is `2048` Q256 units.
QM1 is an oracle ceiling, not a compressed archive.

Bind the parent P1, WRT store, dictionary, raw 10M, page map, and Q256 tables by
exact size and SHA-256 before parsing. Q256 construction is
`tools/mobius2_tessera_typed_fiber_ceiling.py::qbit_tables`: `float64`
`-log2(p) * 256`, `numpy.rint` nearest-even, and canonical little-endian
`int32` serialization. The zero/one table hashes are respectively
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

## Causal graph contract

Graph topology and exact candidate spelling use different identities:

```text
graph node key:
  wikiback.normalize_title(decoded title or target bytes)

candidate identity:
  tuple(event.encoded for every exact WRT event in the target)
```

Normalization is used only to connect an earlier target to the current title.
It does not merge candidate spellings and does not perform redirect or alias
expansion. Retain for every staged edge:

```text
source page ordinal
source link ordinal
normalized target key
complete exact target program
target program start and end event positions
```

Do not use `LinkRecord.target_codes` as the candidate program because it omits
literals, escapes, and controls. Reuse WIKIBACK's decoder-aligned suffix/parser
surfaces, but retain the complete `WrtEvent.encoded` sequence.

Do not publish any node, edge, frequency, degree, or recency record until the
entire source `</page>` is decoded. Publish atomically into:

```text
closed pages by ordinal
incoming source pages by normalized target key
global exact-program occurrence counts
global exact-program distinct-source-page counts
global exact-program last page and link occurrence
```

The current page cannot contribute candidates or control statistics to itself.
The trailing partial page never publishes or scores.

An opportunity is scheduled only when decoded `[[` ends exactly at a WRT-event
boundary. Freeze all lane candidates immediately after that opener event and
before the next WRT bit. Do not retroactively remove the opportunity if the
subsequent target is malformed. A hit exists only if the following complete
exact WRT target program equals one frozen candidate and is immediately
followed by a legal `|`, `#`, or `]]` terminator; otherwise the opportunity is a
zero-ceiling escape.

Use the completed current page title to retrieve strictly earlier closed pages
that linked to its normalized key. Their other target records form `G0`; remove
every record whose normalized target key equals the current normalized title
key.

Merge duplicate exact candidate programs and freeze at most 64, ranked by:

1. descending number of distinct supporting earlier closed pages;
2. descending exact-program occurrence count over all closed pages;
3. descending most recent supporting page ordinal;
4. ascending flattened exact WRT program bytes.

Repeated mentions inside one source page contribute one unit to supporting-page
count but retain their ordinary occurrence count for the second criterion.

Target truth, length, namespace, fragment, delimiter, label, future page
adjacency, final graph degree, and corpus-wide title information are forbidden.
Each exact spelling occupies a separate candidate slot. Redirect expansion,
alias merging, category/template relations, prose entity recognition, and
multi-hop searches outside the frozen co-link composition are excluded.

## Matched lanes

Let `K = len(G0)` after ranking, with `1 <= K <= 64`. Every lane receives the
same pre-truth opportunity and exactly `K` distinct exact-program candidates.
If any causal injective control cannot supply `K`, deactivate the opportunity
for every lane before truth.

- `G0`: exact causal co-link target candidates.
- `Cfreq`: all-closed-prefix exact programs ordered by descending occurrence
  count, then ascending exact program bytes; take the first `K`.
- `Crecent`: all-closed-prefix exact programs ordered by descending last page
  ordinal, descending last link ordinal, then ascending exact program bytes;
  take the first `K`.
- `Cprior`: the latest fully closed page containing at least `K` distinct exact
  target programs. Rank within it by descending within-page frequency, then
  ascending exact program bytes; take the first `K`.
- `Cshuffle`: for each `G0` program, select a different prefix-visible exact
  program from the same matched bin, exclude the complete `G0` set, and require
  an injective result. Bins are `(occurrence_count.bit_length(), flattened
  exact-program byte length, distinct-source-page-count.bit_length())`.
  Candidate substitutes are ordered by SHA-256 over the completed current title
  key, current page ordinal, opportunity ordinal, source program, and candidate
  program. The serialization and field separators are frozen before
  materialization.

All control programs, bins, counts, ordinals, and source pages must come from
fully closed earlier pages and be visible at the opportunity boundary. The
post-truth membership selector is free only for this ceiling.

Repeated construction must reproduce byte-identical digests for parser events,
closed-page publication, graph nodes and edges, opportunity positions,
candidate lists and ranks, control assignments, and per-split totals.

## Exact ceiling accounting

Use `mobius2_tessera_typed_fiber_ceiling.read_p1`, `qbit_tables`, and
`byte_qbits`; `sibyl_page_prompt_oracle.page_intervals` and `write_page_map`;
and the shared exact WRT parser. For a hit, sum Q256 parent loss over the exact
target program event interval. Verify exact parent P1-to-payload identity and
WRT/raw reconstruction before reporting a ceiling.

Apply split thresholds with integers. For raw split size `R` and split Q256
gain `Q`, the `5,000 B/M` condition is exactly:

```text
Q * 1,000,000 >= 5,000 * 2,048 * R
```

Do not round a floating-point B/M display value into a decision.

## Decision rule

Authorize only a separately materialized paid Q0 when all conditions hold:

```text
all graph sources fully closed and strictly earlier        pass
all candidates frozen before the first target bit          pass
pre-truth opportunity and capacity equality                pass
parser/graph/candidate/control replay digests               exact
parent payload, WRT, and raw identities                     exact
Q256 table hashes                                            exact
G0 total                                                    >= 60,000 byte-equivalent
G0 development                                              >= 5,000 B/M
G0 selection                                                >= 5,000 B/M
G0 confirmation                                             >= 5,000 B/M
G0 minus every control, total                               >= 10,000 byte-equivalent
G0 minus every control, each split                          positive
```

Any miss retires this exact co-link composition, 64-entry candidate language,
ranking rule, event universe, and control construction. Do not rescue-sweep
walk depth, relation families, aliases, redirects, normalization, candidate
capacity, score weights, graph caps, or support thresholds.

A pass authorizes only an actual Q0 with finite hit/escape and rank coding,
exact target reconstruction, parent-state-preserving replay, framing,
termination, bounded graph memory, deterministic eviction, and counted source.
Before Q0 is materialized, freeze the actual hit/escape coder, actual rank coder
over at most 64 programs, residual arithmetic stream, complete-page-limit frame,
residual-only tail, compressed source bundle and allowance, graph memory cap,
and eviction order. Q0 must decode both streams, reconstruct WRT and raw,
repeat the archive byte-for-byte, and prove the full Predict plus
Perceive/update transition for bypassed bits. Paid `G0` total must beat every
paid control total.

That Q0 must save at least `30,000` actual bytes on canonical 10M and satisfy:

```text
gross_B_per_M - compressed_package_bytes / 1000 >= 2,100 B/M
```

The JANUS-plus-quotient trace is an attribution parent only. No QM1 or paid
trace-Q0 outcome earns forecast credit or authorizes a larger population.
Score credit requires fresh native endpoint428 integration and joint replay.
