# WikiIR-MDL

WikiIR-MDL is the primary orthogonal representation research program for
`enwiki9`.  It is not another probability router over the current FX2 or
CMIX21 endpoints.

The objective is a reversible compiler that exposes several descriptions of
the same Wikipedia span and pays for the cheapest complete description:

```text
enwik9 bytes
  -> exact typed Wiki/XML IR
  -> literal | tree grammar | prototype delta | graph | columnar
  -> exact MDL selection with all inverse metadata counted
  -> compact CMIX21 or FX2-compatible literal backend
  -> archive
```

Only a full `1,000,000,000`-byte roundtrip with official score at or below
`109,500,000` proves the target.  IR, oracle, proxy, and prefix results are
discovery evidence only.

## Why This Is A Different Search Direction

The current endpoint428 lane changes a probability blend while preserving the
same symbol stream.  WikiIR-MDL changes the available descriptions:

- grammar rules expose repeated typed structures with holes;
- prototype deltas expose similarity between whole pages;
- graph coding exposes repeated link and category neighborhoods;
- columnar blocks expose repeated fields and value types;
- token sequence models expose long WRT contexts across typed regimes.

An endpoint router can only choose among probabilities it is given.  An IR
compiler can create COPY, RULE, RUN, field, edge, and delta events that those
predictors never observe.

## Measured Creative Probe Ledger

The measured discovery populations now have sixteen exact probe receipts. These rows
do not change the score forecast:

| Probe | Reversible signal | Exact backend result | Decision |
|---|---:|---:|---|
| Ordered template skeleton grammar | `3,735` fewer raw IR bytes; `17` rules and `313` references | LZMA archive regressed `1,208` bytes; literal MDL fallback selected | Retire this global LZMA serialization; retain typed holes for target-backend or columnar tests |
| Prior-page ADD/COPY/RUN delta | `112,287` fewer raw IR bytes; `168,837` bytes copied across `170/171` pages | Interleaved LZMA archive regressed `24,192` bytes; literal fallback selected | Explicit byte commands expose real structure but serialize it worse than a mature local matcher |
| Prior-page IR on target backend | Exact raw-to-IR inverse; guarded hybrid encode stayed `701,133` KiB below the decimal limit | `200,865` bytes versus the complete native hybrid archive `173,963`, a `26,902`-byte regression | Retire this ADD/COPY/RUN event universe on the target backend; do not tune or scale it |
| Nested columnar prior-page commands | Reconstructs the byte-identical interleaved IR and raw input | Recovers `10,372` bytes versus interleaving but remains `13,820` bytes behind literal LZMA | Retire this fourteen-stream LZMA bundle; do not retire columnar typed fields generally |
| Bounded integer Sequence Memoizer | `473,276` completed WRT tokens; `500,000` contexts; deterministic Q24 updates | Exact hybrid replay saves `1` byte overall and `1` byte held out, with `3` regressing blocks | Retire untyped token-suffix HPYP; Skip-CTS must add page/field state or a different endpoint |
| Repeated-link graph dictionary | `452` front-coded targets and `1,695` ordered occurrences remove `18,046` raw bytes | LZMA loses `1,916`; guarded hybrid archive is `177,190` versus `173,963`, a `3,227`-byte regression | Retire generic target factoring in this layout; title-as-vertex factoring or actual adjacency referentiation must create a different event universe |
| Front-table title graph | `172` titles and `147` exact links remove `2,393` raw bytes | Guarded hybrid archive is `174,550` versus `173,963`, a `587`-byte regression | Retire the copied-title dictionary layout |
| Tail-table title graph | Identical selected titles/links with the skeleton first; removes `2,388` raw bytes | Guarded hybrid archive is `174,515` versus `173,963`, a `552`-byte regression | Metadata placement recovers only `35` bytes; retire this serialization |
| Dictionary-free two-pass title graph | Preserves literal titles, supports forward references, and maps `216` exact/normalized links; removes `3,967` raw bytes | LZMA saves `52` bytes before mode, but the guarded hybrid is `174,134` versus `173,963`, a `171`-byte regression. At `10M`, `2,556` links remove `20,682` raw bytes but LZMA loses `28`. | Retire unchanged preprocessing. Preserve the two-pass inverse idea for other event universes and move title reuse into a direct WRT probability endpoint. |
| Causal page-list COPY/ADD delta | Earlier-page overlap is genuine: the target-list-only control finds `2,399` bytes over deterministic random at `1M`. The complete transform retains only `539` bytes across `15/171` pages after escaped raw skeletons, references, and inverse commands. | Exact materialization is `1,000,174` bytes (`-174` raw delta); LZMA is `291,900` versus literal `290,732`, a `1,168`-byte regression. Raw and archive inversion are deterministic. | Retire this link-target skeleton and COPY/ADD serialization. The overlap does not justify a target-backend gate; revisit only with a page-scoped event that shares more than target strings. |
| Same-skeleton prior-page template values | `169` template occurrences have an earlier complete-page occurrence with the same ordered skeleton, but only one repeated field is even recoverable and its COPY command costs more than the value. Matched prior-selection and random controls both save `0`. | The exact MDL headroom is zero before raw surface, IR, backend, or source costs. | Retire same-field value COPY as a page-prototype event. Do not build a full transform; a successor must exploit typed reference/URL/date structure, not generic repeated template values. |
| Self-trained URL-host dictionary | The decoder learns `396` hosts from literal prefix URLs and replaces `109` later hosts, removing `1,401` raw IR bytes with no static dictionary. The exact inverse, compressor roundtrip, and repeated archive are deterministic. | LZMA archive is `290,956` versus literal `290,732`, a `224`-byte regression before the mode byte. | Retire this host-reference serialization without a target-backend gate. Preserve the self-trained typed-dictionary mechanism only for a richer URL/reference event that can also exploit paths, dates, or citation field structure. |
| Self-trained URL host-plus-first-path dictionary | The decoder reconstructs `396` hosts and `434` prefixes from prior literal URLs, then uses `42` host and `67` prefix references. The exact inverse removes `1,852` raw IR bytes and is deterministic. | LZMA archive is `290,932` versus literal `290,732`, a `200`-byte regression before the mode byte. The extra path structure recovers only `24` compressed bytes over host-only reuse. | Retire this URL-prefix serialization unchanged. Do not run the target backend; the local control is terminally negative before mode or source cost. |
| Citation-field columnar values | Exact inversion removes selected URL/date/person/title values from completed citation templates and streams them by semantic key; ordinal buckets are the matched layout control. | Across two random windows per scope, the all-field semantic form loses `232` LZMA bytes at `500K` and `144` at `1M`; every semantic LZMA family is non-positive and semantic grouping does not consistently beat control. | Retire this field-columnar serialization without a target-backend gate. Sparse citation values do not pay framing or recover independent backend information. |
| Decoder-built named-reference interning | Full-corpus census finds `2,375` names, `755` repeat occurrences, and only `11,363` maximum raw bytes before container and code costs. | The raw ceiling is already below the `57,404`-byte endpoint428 debt; sampled windows contain no events and show only framing loss. | Retire as a primary component by impossibility bound. A broader reference mechanism may reuse the parser, but name interning cannot close the target. |
| Same-skeleton reference COPY/ADD | A causal last-16 retrieval search over `7,055` complete reference bodies finds `1,854` paying events and `125,092` raw MDL bytes, enough discovery headroom before backend effects. | Both exact layouts fail: columnar loses `464`/`1,968` LZMA bytes versus raw on dense `500K`/`1M`, while inline loses `1,008`/`2,976`; both are worse than matched literal containers. Every inverse passes. | Retire both serializations unchanged. The oracle is information already captured by mature backend context; revisit only as a target-residual probability endpoint, not another COPY/ADD layout. |

The earlier raw-MDL screen estimated `1,856` bytes for host-plus-first-path
reuse. The exact four-byte-framed inverse realizes `1,852` bytes, so the
screen-to-construction transfer is understood; the remaining failure is backend
economics, not reversibility or hidden dictionary cost.

Receipts and exact artifacts are under `/home/x/enwiki9-nonproof/results/` with
the `wikiir_` and `wrt_sequence_memoizer_` prefixes.  The target-backend
receipts include `wikiir_prior_page_delta_1m_v1_hybrid_screen.json`,
`wikiir_webgraph_1m_v1_hybrid_screen.json`, the `wikiir_title_vertex_*`
screens, and `wikiir_page_list_delta_1m_v1_materialization.json`.  They settle the measured
serializations negatively without claiming codec proofs: each exact raw-to-IR
inverse passed and each guarded encode completed, but backend decode was
intentionally skipped after the terminal archive-size miss.  Schema v2 compares
complete native archives on both sides; an earlier payload-only baseline
comparison overcharged each WikiIR candidate by `37` bytes and was corrected.
The newer local random-window receipts are
`results/wikiir_citation_field_columnar_random_v1/selection.json`,
`results/wikiir_named_ref_intern_random_v1/selection.json`, and the two
`results/wikiir_reference_delta_random_v1/selection_*_dense.json` layouts.

## Exact Typed IR Contract

The parser must retain enough surface information to reproduce every input
byte.  Initial event families are:

```text
raw literal
XML open, close, attribute, text, entity
page and title
template name, argument key, argument value
link target and label
reference field
table row and cell
list item
URL
number, date, and punctuation shape
```

Whitespace, quoting, capitalization, escaping, argument order, malformed
markup, and parser fallback bytes are part of the IR or an explicit surface
stream.  Malformed input always has a literal escape.  The first proof is
parser roundtrip and deterministic event hashes, not compression.

## Representation 1: Parameterized Wiki Tree Grammar

Build bounded-rank straight-line tree rules over typed XML and wikitext nodes.
A rule may contain holes for values while preserving exact formatting, for
example a citation skeleton with URL, title, and date arguments.

Rule selection is MDL-based:

```text
rule value = displaced literal/backend bits
           - rule definition bits
           - invocation and argument bits
           - surface and position bits
           - decoder/code cost allocation
```

Frequency alone is not an admission rule.  Search may use TreeRePair-style
digram replacement, bounded-rank subtree mining, stable locally consistent
cores, beam search, or large-neighborhood replacement.  The final grammar,
arguments, and inverse formatting are explicit and counted.

Foundation:

- [TreeRePair](https://doi.org/10.1016/j.is.2013.06.006) generalizes Re-Pair to
  straight-line context-free tree grammars with parameters.
- [Stable local consistency](https://doi.org/10.4230/LIPIcs.SEA.2025.14)
  supplies a scalable way to give repeated patterns consistent grammar cores.

First artifact:

- typed-IR roundtrip receipt;
- rule definition and use ledger;
- literal bits displaced and complete inverse cost;
- exact target-backend archive delta on train, development, and untouched
  page groups;
- deterministic grammar and archive hashes.

## Representation 2: Prior-Page Prototype Delta

For each page, retrieve structurally similar earlier pages from deterministic
title, template, category, and typed-event signatures.  The encoder evaluates
the current complete page and emits an explicit prior-page reference plus an
edit program:

```text
COPY prior interval
ADD literal or typed events
RUN repeated event
```

The reference is always to already reconstructed data.  Candidate discovery
may use minimizers or sketches, but decoder correctness depends only on the
encoded reference and edit program.  This follows the portable delta contract
of [VCDIFF](https://www.rfc-editor.org/rfc/rfc3284) and the collection-level
motivation of [Relative Lempel-Ziv](https://arxiv.org/abs/1106.2587).

First artifact:

- deterministic prior-page candidate index;
- explicit reference and edit streams;
- exact page and corpus roundtrip;
- command, address, length, literal, and source-code bytes counted separately;
- matched random-prototype control and disjoint page-family results.

This is also the constructive successor to the failed token-span probability
selectors: encode candidate rank and match length instead of attempting to
predict the winning candidate bit by bit.

## Representation 3: Wikipedia WebGraph Codec

Extract page-local sequences of link targets, categories, templates, and
reference targets.  Encode a list relative to a similar earlier list using:

- copied intervals;
- intervalized consecutive identifiers;
- sorted residual gaps;
- compact integer codes;
- a counted position/permutation stream that restores original occurrence
  order.

The mechanism is motivated by [WebGraph](https://vigna.di.unimi.it/ftp/papers/p595-boldi.pdf),
whose reference and interval methods compress web adjacency lists strongly.
Its published web-graph rates are context, not a forecast for Wikipedia.

The decisive result is the total archive after target IDs, positions,
reference choices, residual gaps, and implementation bytes are counted.

## Representation 4: Nested Columnar Template Blocks

Buffer bounded page groups and transpose repeated nested fields into streams
such as:

```text
template id
argument key id
value type
value
repetition and definition levels
surface position
```

URLs, dates, numbers, repeated keys, and citation values then receive
dictionary, delta, run-length, grammar, or literal coding appropriate to the
column.  [Dremel](https://research.google/pubs/dremel-interactive-analysis-of-web-scale-datasets/)
provides the nested-record columnar representation precedent; WikiIR-MDL must
add an exact surface-order inverse and compression accounting.

## Endpoint 5: Typed Token Sequence Memoizer

Build a bounded deterministic approximation to a hierarchical Pitman-Yor
sequence model over WRT tokens, partitioned by title, prose, template value,
reference, URL, table, and number regimes.  The
[Sequence Memoizer](https://www.stats.ox.ac.uk/~teh/research/compling/GasWooTeh2010a.pdf)
demonstrates incremental unbounded-context modeling for lossless compression.

The submission form must use integer or otherwise cross-platform deterministic
updates.  No sampling, hidden weights, or external state may affect decoding.
It competes against the exact literal backend on identical token rows.

## Endpoint 6: Skip Context Tree Switching

Use bounded skip contexts over typed records so template keys, page family,
bit or token position, and prior values can condition prediction while
irrelevant intervening values are ignored.
[Skip Context Tree Switching](https://proceedings.mlr.press/v32/bellemare14.html)
provides Bayesian averaging and switching over prediction suffix trees that
can skip contiguous context portions.

This is a new endpoint only if its probability is measured incrementally
against the exact target substrate.  Generic CTW accuracy is not evidence.

## Endpoint 7: Self-Trained Page-Family Micro-Models

Deterministically train small fixed-point predictors from previously decoded
members of recurring page or template families.  No weights are shipped.
Updates, resets, family membership, and inference are reproduced from the
decoded prefix.  These models compete directly with the Sequence Memoizer and
Skip-CTS on the same sealed traces.

## Exact MDL Selection

For every span and representation:

```text
net bits = literal/backend bits displaced
         - mode and command bits
         - rule, reference, and inverse-formatting bits
         - table, dictionary, model, and source-package bits
         - integration regressions
```

Representation choices interact through backend state, so independent local
scores may be misleading.  Discovery may use dynamic programming, beam
search, integer programming, e-graphs, simulated annealing, or
large-neighborhood search.  The final choice stream is explicit; the decoder
does not reproduce the NP-hard search.

Each candidate must include a literal fallback.  Selection is frozen on
training/development page groups, then evaluated once on untouched groups.
Report gain concentration by page family and corpus region.

## Priority And Demotions

The first parameterized grammar, prior-page delta, nested-columnar delta,
generic repeated-link dictionary, three title-graph layouts, and untyped
Sequence-Memoizer shapes are now measured and retired.  Run the next
orthogonal descriptions in this order:

1. direct WRT entity continuation: build a decoder-reconstructed trie from
   completed title and link event sequences, activate it only within link
   targets, and score it incrementally against exact FX2 probabilities;
2. typed template/reference/URL columns or a prior-page prototype delta that
   replaces more than isolated link targets;
3. typed-field Skip-CTS over page/template/reference/URL state;
4. a different parameterized grammar whose events remain useful to the target
   backend rather than expanding into byte-level ADD/COPY/RUN commands.

Article-order TSP is demoted because inverse-permutation cost and prior GEPA
failures reduce its expected leverage.  Generic residual decision-DAG search
is demoted until a new endpoint or representation supplies paying signal for
it to compile.

The endpoint428 matched trace remains a bounded conversion experiment.  It
does not block these WikiIR-MDL probes and receives no native weight ladder.

## Promotion And Kill Gates

A WikiIR component advances only when it has:

- exact IR and raw-byte roundtrip;
- deterministic output and state hashes;
- train/development/untouched page-group separation;
- a literal anchor and a matched complexity or retrieval control;
- gross and net exact bytes with every inverse stream and source byte counted;
- bounded memory and an implementation path compatible with the official
  runtime;
- substantial disjoint margin over the current per-million-byte debt.

Retire an implementation shape when its exact command or inverse cost consumes
the structural gain.  Do not infer that the representation family is false
from one weak parser, candidate generator, integer code, or backend layout.
