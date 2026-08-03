# WIKISECTION exact-heading prefix-guard QM1 v2 addendum

Candidate: `wikisection_exact_heading_body_lexicon_prefix_guard_qm1_v2`

Parent realization: `wikisection_exact_heading_body_lexicon_qm1_v1`

The first v1 execution terminated as malformed evidence before scoring. The
accepted heading `====Troilus====` exposed a dictionary token as `PROSE_WORD`:
after the four opening equals, the generic role classifier interpreted the
completed `====` prefix as a possible empty closing delimiter. This violated
the frozen requirement that an accepted heading contain zero scheduled token
opportunities. It was not a compression result.

V2 changes only the causal opportunity guard. At a pre-event boundary, suppress
an opportunity while the completed current-line prefix can still begin an
accepted exact heading:

```text
empty line                         not suppressed
one through six leading '=' bytes suppressed
one leading '=' then non-'='       no longer suppressed
two through six leading '=' bytes suppressed for the rest of the line
seven or more leading '=' bytes    no longer suppressed
```

The first unknown event on an empty line remains scheduled. If it is an equals
literal, it is not a dictionary-token hit; after that literal is decoded the
prefix guard is active. The rule is therefore causal and does not inspect the
current event kind or truth. It conservatively suppresses some non-heading
prefix opportunities but can never schedule a dictionary token on a line that
later satisfies the frozen heading grammar.

Everything else is inherited unchanged: inputs, exact heading grammar,
normalization, section boundaries, page-close publication, complete-page
population, four candidate lanes, injective capacity matching, Q256 tables,
60/20/20 splits, integer thresholds, replay requirements, and three-way
decision. V2 is the one infrastructure correction for v1, not a parameter or
information-source sweep.
