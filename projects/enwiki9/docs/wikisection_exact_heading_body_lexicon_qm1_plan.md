# WIKISECTION exact-heading body-lexicon QM1 plan

Candidate: `wikisection_exact_heading_body_lexicon_qm1_v1`

Status: proposed and dormant until the WIKIBACK QH0 decision

Evidence level: zero-credit optimistic causal information ceiling

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

At a decoder-visible line start, accept a heading only when it has an opening
run of two through six `=` bytes, a balanced closing run of the same width, and
a completed newline. Headings are non-nested. Normalize the heading body by
trimming outer ASCII whitespace, ASCII-lowercasing, converting underscore to
space, and collapsing ASCII whitespace. Do not apply Unicode normalization,
entity expansion, semantic labels, page labels, or a global corpus index.

A section body begins after the completed heading newline and ends at the next
completed heading or `</page>`. Stage exact dictionary-token WRT events locally.
Publish section records only after the enclosing page closes, so neither the
current section nor any later content from its page can train its own snapshot.

At heading completion, snapshot all records from earlier completed pages under
the exact normalized heading. Before each later decoder-visible `PROSE_WORD`
event, an optimistic hit exists only when the current exact encoded WRT token is
present in that frozen snapshot. The current event kind, truth, length, and
future page state are unavailable when the opportunity is declared.

## QM1 controls

QM1 supplies the index, counts, selector, ranks, source, framing, and stream
termination for free. It measures only rounded-Q256 JANUS-plus-quotient
codelength displaced by exact-token hits. It is not a codec result.

All lanes use identical pre-truth opportunities and injective capacity
matching. If a control cannot supply the exact-key unique count from completed
prior state, deactivate that section for every lane.

```text
Hblind  an earlier different-heading body lexicon, selected by minimum
        unique-count bit-length distance and earliest-page ties
Hprior  the immediately previous completed-page token reservoir
Hcoarse prior bodies sharing only the frozen retired ten-state heading class,
        deterministically truncated to the exact-key unique count
Hexact  prior completed bodies under the exact normalized heading
```

## Frozen decision

Require all of:

```text
parent input identities                         exact
parser/index replay                             byte-identical
opportunity and control digests                 byte-identical
all candidates sourced from prior closed pages exact

Hexact full free displaced ceiling              >= 60,000 bytes
Hexact each chronological split                 >= 5,000 B/M
Hexact - max(Hblind,Hprior,Hcoarse), full        >= 10,000 bytes
Hexact control margin on every split            positive
```

A valid miss retires this exact heading grammar, normalization, section-body
event universe, page-close commit policy, and matched controls. Do not sweep
heading width, support, normalization, section windows, or coarse classes.

A pass authorizes only one Q0 with an actual finite Q24 per-section KT
hit/escape stream, frozen hit-rank stream, distinct residual arithmetic
payloads, decoder-built opportunity schedule, exact WRT/raw inverse, repeated
archive identity, at least 30,000 gross bytes, positive opened splits, at least
2,100 B/M after measured compressed source, and `Hexact` below every control.
Q0 remains zero-credit.

If WIKIBACK rejects, Q0 compares against the exact joint parent. If WIKIBACK
passes, the primary Q0 must be a joint WIKIBACK plus WIKISECTION replay with one
frozen precedence rule and both side costs, measuring only incremental events
not already bypassed. Separate gains and forecasts must never be added.

