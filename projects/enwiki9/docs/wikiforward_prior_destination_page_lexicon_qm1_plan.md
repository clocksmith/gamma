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

Use the canonical opening-10M inputs and exact WRT/page/link grammar already
bound by `docs/wikiback_incoming_anchor_context_qh0_plan.md`:

- the exported JANUS-plus-quotient adjusted P1 trajectory;
- its matching truth and WRT streams;
- exact complete-page boundaries and title/link parsing;
- the official WRT-to-raw inverse receipt;
- chronological complete-page splits of 60%, 20%, and 20%;
- the trailing partial page is parsed for integrity but contributes no active
  WIKIFORWARD opportunity.

All rounded loss is measured in Q256 bits. One byte-equivalent is exactly
`2048` Q256 units.

## Causal contract

For every complete page, maintain a lexicon containing only lexical WRT events
already decoded in that page. A link target becomes actionable only after its
final target byte and closing syntax are decoded. If the exact target resolves
canonically to an earlier completely closed page, add that destination page's
completed `PROSE_WORD` event lexicon to the current page's active destination
source.

Only later `LINK_LABEL` and `PROSE_WORD` events may be scored. At the prediction
boundary, the event's truth, eventual length, and future page bytes are not
visible. The optimistic membership decision is evaluated after truth solely
to measure the free ceiling. A qualifying hit must be absent from the exact
already decoded current-page prefix lexicon.

The destination lexicon is immutable after its source page closes. Resolve
targets with exactly the frozen WIKIBACK ASCII normalization and no additional
Unicode, entity, redirect, semantic, or alias normalization. Unresolved
targets, later pages, the current destination event, future links, and
encoder-only aliases are forbidden. A source page must have a strictly smaller
completed-page ordinal than the current page. If a normalized title key maps
to more than one earlier closed page, deactivate that target rather than
choosing among duplicate destinations.

A destination lexicon contains only exact encoded WRT dictionary-token events
whose pre-event role is `PROSE_WORD`. Current-page prefix novelty is defined
over every previously decoded exact WRT dictionary-token identity in every
role; an identity previously seen in markup, a heading, link syntax, or another
role is therefore not novel.

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

## Exact QM1 lanes

All lanes must receive the same causally visible resolved-target updates. They
must expose identical opportunity positions and identical cumulative unique
lexeme count and weight multisets before truth is examined.

- `Dfull`: lexicons of the exact earlier destination pages named by completed
  current-page outgoing links.
- `Dblind`: unrelated earlier closed pages selected deterministically and
  injectively, matched to each destination update by destination-page lexicon
  size. Store source ordinal and normalized title key and require that key to
  differ from the real destination key.
- `Dprior`: page ordinal `current_page_ordinal - 1` when that page is fully
  closed and has an eligible prose lexicon, capacity matched to the same
  destination update; otherwise the update is unavailable to every lane.
- `Dglobal`: globally frequent prior identities selected from completed pages,
  capacity matched to the same destination update. Global counts update only
  after the contributing page closes.

At every opportunity, rebuild each control from its frozen causal source
reservoir after current-prefix exclusion. Assign the current `Dfull`
prefix-novel weight multiset injectively to each control. A match made at the
earlier destination-update boundary is not sufficient because later prefix
events can remove different identities from different lanes. If any control
lacks capacity at the current opportunity, deactivate that opportunity for
every lane. No lane may receive an extra opportunity.

The following repeated-build digests must be byte-identical:

- exact parser events and page/title/link boundaries;
- prior-page title index and destination resolutions;
- opportunity positions and prefix-novel masks;
- per-update control assignments and capacity multisets;
- per-lane rounded-Q256 totals and split totals.
- exact joint-parent payload bytes and SHA-256;
- exact decoded WRT bytes and official raw inverse SHA-256.

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
