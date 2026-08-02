# WIKIBACK incoming-anchor-context QH0

Proposal:
`wikiback_incoming_anchor_context_qh0_v1`

## Claim boundary

WIKIBACK is a zero-credit exact ceiling over the canonical opening 10M
population. It asks whether completed earlier backlink neighborhoods predict
exact lexical events in the page they point to, beyond the exported
JANUS-plus-quotient trajectory. It is not a forecast input or constructive
codec until a counted native implementation exists.

```text
target                         108,000,000 bytes
verified full-1G result        unknown
best counted forecast          109,389,323 bytes
remaining forecast debt          1,389,323 bytes
new score credit                         0 bytes
```

The post-TESSERA portfolio requires a new source of prose-token identities.
The page-roster screen found that `LINK_TARGET` was the only tested lexical role
positive on every chronological split, although its optimistic 10M ceiling of
`23,001.499` bytes missed the `30,000`-byte gate. WIKIBACK does not reuse the
within-page roster. It asks whether the lexical material surrounding prior
incoming links transfers to the body of their target page.

A read-only hypothesis audit over the 1,325 complete opening-10M pages found
completed prior backlink contexts for `105/265` selection pages and `102/265`
opened-confirmation pages. Exact tokens present in those contexts covered `17.707%` and
`15.274%` of raw lexical occurrences. A weak exploratory backlink/unigram
mixture beat its development unigram reference by approximately `7,010` and
`4,889` bytes on those two opened splits. These figures are not exact codec
evidence and receive zero credit; they authorize only this one frozen ceiling.

## Frozen causal source

Stage every event and link target while a page is decoded. A record begins at
an outermost decoded `[[`. Its target ends at the earliest `#`, `|`, or `]]`.
The grammar is nonrecursive: a nested `[[` inside an active record is ordinary
target/label content. Delimiters that split a WRT event discard that record.
Only dictionary-token WRT events are lexical candidates. `Ctarget` contains the
target tokens only. `Wfull` contains those target tokens plus the nearest up to
16 token events ending before `[[` and the nearest up to 16 token events after
the target terminator (therefore including a label/fragment when present).
Only after exact `</page>` close are those records committed.
The record becomes visible only after the entire earlier page and both sides of
the context have been decoded. Current-page self-seeding is impossible.

Apply one identical transform to completed link targets and completed titles:
first remove bytes beginning at `#`, then ASCII lowercase, convert underscore
to space, and trim/collapse ASCII whitespace. When a later page title has been
fully decoded, snapshot all already committed records whose normalized target
equals that title. No Unicode normalization, entity
unescaping, namespace knowledge, redirect graph, page label, global title map,
future link, eventual event length, or encoder-only neighbor is permitted. No
later incoming link may alter the active page snapshot.

Before each WRT event, derive the structural role from already decoded Wiki
state. Whenever that pre-event role is `PROSE_WORD` and the frozen page snapshot
is nonempty, code exactly one of:

```text
HIT(exact lexical event rank)
ESC(parent-coded exact event)
```

The opportunity is therefore known before any current-event truth or event kind
is read. Every active occurrence goes through this alphabet. Each variant
resets page-local counters `hit=escape=0` at snapshot time. The Q24 tag coder
uses integer weights `2*hit+1` and `2*escape+1`, scores the tag, reconstructs or
decodes the event, and only then increments the decoded tag's counter. It never
derives a count from current-page truth. Hit ranks use frozen
snapshot occurrence counts projected to a legal Q24 CDF with canonical exact
encoded-event ordering for ties. `ESC` consumes exact JANUS-plus-quotient truth
bits until the WRT parser recognizes the completed event. There is no
truth-aware occurrence selector.

In a native child, every reconstructed hit bit must still update the parent so
the state after each event equals ordinary replay.

Canonical 10M contains 1,325 closed pages followed by an opened but incomplete
1,326th page. The counted archive frame transmits the 1,325 complete-page limit.
The decoder may stage the trailing partial page but disables WIKIBACK there,
codes its entire tail through the parent residual, and never commits it to the
backlink index. A completed page beyond the transmitted limit is malformed.

## Exact opening-10M controls

Use the receipt-bound `joint_candidate.p1`, matching WRT truth and store,
official inverse dictionary, exact page map, and raw 10M input.

```text
B0       exact joint parent
Ctarget  exact lexical events inside the completed incoming-link targets,
         excluding the +/-16 surrounding context
Cblind   same candidate count and weight multiset as Wfull, but candidate
         identities taken from a deterministic unrelated completed-page Wfull
         snapshot
Cprior   same-sized identities from the immediately previous completed page
Wfull    full incoming-anchor contexts
```

Cblind and Cprior must never use a future page. Cblind selects among earlier
saved Wfull snapshots with enough unique identities by minimum unique-count
bit-length distance, then earliest page ordinal. Candidate construction is
injective over exact encoded events. If either completed reservoir cannot supply
Wfull's unique candidate count, the page is deactivated for every variant.
Otherwise assign Wfull's descending weight multiset to source-frequency-then-
byte-ordered unique identities. Cprior is a topic/cache control;
Ctarget isolates the link target only. Every control uses the same active page
and pre-truth event opportunities as Wfull. A future/circular page
rotation may be reported only as a nonconstructive diagnostic and cannot enter
the promotion inequality.

For each variant, construct and terminate an actual finite Q24 event side stream
and an actual residual arithmetic stream. Its decoder must stream the side tag:
on HIT it reconstructs the exact event and advances parent P1 rows without
consuming residual bits; on ESC it consumes parent-coded bits until that event
completes. No externally supplied skip mask, opportunity mask, page map,
snapshot, or learned table may enter decode. Reconstruct the complete WRT,
apply the official inverse, and repeat the full model/index/side/residual/archive
build. Log model/source/framing bytes even though QH0 grants no score credit.

## Chronological discipline

```text
development                    first 60% of complete pages
selection                      next 20%
opened confirmation            final 20%
```

The title normalization, context width, event roles, KT initialization, Q24 rank
coder, control construction, source allowance, and all tie rules are frozen
before the run. All three opening-10M splits have already been inspected by
prior screens, so none is labeled sealed or untouched. Split contributions are
diagnostics inside one chronological causal replay; the backlink index is never
reset merely to measure a split. If QH0 passes, the frozen distant replay is the
first untouched confirmation.

## Decision

Let `T(v)` include the actually terminated residual, event side stream,
framing, and frozen compressed source allowance. The provisional QH0 allowance
is zlib level-9 compression of one canonical bundle containing the plan, tool,
and every direct imported project donor, each byte-identical to the recorded Git
commit, plus 64 source-framing bytes. Require it to be at most `196,608` bytes.
With allowance `P`, report `net_B/M = gross_B/M - P/1000`. This is a ceiling
charge, not a constructive native package claim. Require all of:

```text
joint parent identity                         exact
side and residual arithmetic decode           exact
complete WRT and raw reconstruction            exact
causal prior-page-only backlink index          exact
second model/side/residual replay               byte-identical
all probabilities and CDF frequencies          legal and nonzero

development Wfull contribution                 positive
selection Wfull contribution                   positive
opened-confirmation Wfull contribution         positive
B0 - Wfull                                     >= 30,000 bytes
Wfull projected package-adjusted gain           >= 2,100 B/M
T(Wfull)                                        < T(Ctarget)
T(Wfull)                                        < T(Cblind)
T(Wfull)                                        < T(Cprior)
```

A valid miss is `REJECT` with process status zero. It retires this exact
incoming-link source, `+/-16` lexical-event context, snapshot rule, KT coder,
and matched controls without context-width, smoothing, normalization, rank,
support, or mixture rescue sweeps.

A pass authorizes only one frozen distant replay, which is the first untouched
confirmation, and a native state-preserving
update proof. It does not change the forecast or authorize 100M or 1G.
