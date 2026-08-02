# MÖBIUS-2 JANUS parity token-fill ceiling QH0

Proposal: `mobius2_janus_parity_token_fill_ceiling_v1`

Candidate: `mobius2_janus_parity_token_fill_ceiling_qh0_v1`

## Question

Does a two-pass lexical event order expose at least 30,000 exact bytes of
information absent from the canonical JANUS-plus-quotient 10M trajectory?

This is not another token suffix predictor. The bounded Sequence Memoizer and
legal typed Skip-CTS already close causal token-suffix modeling. QH0 instead
changes the factorization of prose-token identities within each complete page:

```text
pass 1: token positions 0, 2, 4, ...
pass 2: token positions 1, 3, 5, ...
```

When pass 2 begins, both adjacent even-position anchors are already decoded.
The right anchor is therefore decoder-visible within the side-stream order,
not future truth.

## Frozen population and event universe

Use the canonical opening-10M WRT store and exact exported
JANUS-plus-quotient P1. Only complete-page events whose decoder-built role is
`PROSE_WORD` and whose WRT event kind is `token` enter the side stream. Every
other WRT byte remains on its exact joint P1 row.

QH0 supplies the prose-token position schedule, lexeme catalog, exact WRT
variant catalog, static tables, and implementation free. It still pays every
lexeme symbol, exact WRT variant, side-stream termination byte, residual
arithmetic bit, and 80-byte finite archive frame. This is deliberately an
optimistic ceiling: failure before schedule/table/source cost retires the
family.

Complete pages are split chronologically 60/20/20. Only development pages
build counts. Selection and sealed pages never update the model.

## Static PPM factorization

Each token is factored into a canonical lexeme and its exact WRT byte-program
variant. All distributions are deterministic Q24 largest-remainder CDFs with
nonzero frequencies. Context distributions use an explicit escape and back
off to the development unigram; pair contexts first back off to the matching
left-anchor context. Page state resets at every page.

Frozen variants:

```text
U0  global lexeme unigram
C1  original-order previous-token PPM control
FL  parity order; odd tokens use only the left even anchor
FB  parity order; odd tokens use the true left and right even anchors
FR  parity order; replace the right anchor with the next decoded even anchor
```

FR preserves the same page, pass order, table family, and decoder visibility
while destroying immediate right-neighbor alignment.

## Exact gate

Require:

```text
joint parent payload replay                    byte-identical
side decode for U0/C1/FL/FB/FR                exact
residual arithmetic decode                     exact
complete WRT reconstruction                    exact
official WRT inverse                           exact raw 10M
second model and every archive                 byte-identical
all CDF frequencies                            legal and nonzero
development, selection, sealed FB gain         positive
FB total                                       < U0, C1, FL, and FR
FB gain over joint                             >= 30,000 bytes
```

A valid miss exits zero. Do not sweep parity stride, reveal order, smoothing,
context depth, vocabulary, page reset, token role, or coder precision. A pass
authorizes only a paid schedule/table/source gate; it grants no score or
forecast credit and does not authorize native integration.
