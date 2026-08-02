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

## Causal graph contract

For each fully closed page, store:

```text
exact page-title WRT program -> exact link-target WRT programs in that page
```

Do not publish any node or edge until `</page>` is completely decoded. The
current page cannot contribute candidates to itself. At the first bit after an
eligible `[[`, use the already completed current page title to retrieve all
strictly earlier closed pages that linked to it. Their other exact target
programs form the `G0` candidate universe.

Freeze at most 64 exact target programs, ranked by:

1. number of distinct supporting earlier pages;
2. prefix-observed exact-target frequency;
3. most recent supporting closed page;
4. canonical WRT byte order.

Target truth, length, namespace, fragment, delimiter, label, future page
adjacency, final graph degree, and corpus-wide title information are forbidden.
Each exact spelling occupies a separate candidate slot. Redirect expansion,
alias merging, category/template relations, prose entity recognition, and
multi-hop searches outside the frozen co-link composition are excluded.

## Matched lanes

Every lane receives the same pre-truth eligible target boundaries and the same
candidate capacity. Deactivate an opportunity for every lane if a causal
injective match cannot be constructed.

- `G0`: exact causal co-link target candidates.
- `Cshuffle`: prefix-visible target identities shuffled within matched
  frequency, WRT-length, and visible-degree bins.
- `Cfreq`: most frequent exact targets in the decoded prefix.
- `Crecent`: most recent exact targets in the decoded prefix.
- `Cprior`: exact targets from matched immediately prior closed pages.

All shuffled nodes, degrees, frequencies, and source pages must already be
visible at the opportunity boundary. The post-truth membership selector is
free only for this ceiling.

Repeated construction must reproduce byte-identical digests for parser events,
closed-page publication, graph nodes and edges, opportunity positions,
candidate lists and ranks, control assignments, and per-split totals.

## Decision rule

Authorize only a separately materialized paid Q0 when all conditions hold:

```text
all graph sources fully closed and strictly earlier        pass
all candidates frozen before the first target bit          pass
pre-truth opportunity and capacity equality                pass
parser/graph/candidate/control replay digests               exact
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
That Q0 must save at least `30,000` actual bytes on canonical 10M and project at
least `2,100 B/M` after package accounting. No QM1 outcome earns forecast
credit or authorizes native integration or a larger population.
