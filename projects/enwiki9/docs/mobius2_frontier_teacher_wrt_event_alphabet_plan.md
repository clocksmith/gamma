# MÖBIUS-2 frontier-teacher WRT event alphabet QH0

Candidate: `mobius2_frontier_teacher_wrt_event_alphabet_qh0_v1`

Status: zero-credit dynamic-event-alphabet ceiling. This is not a codec,
source-bound score, teacher package, or permission to ship a language model.

## Question

Can a causal language teacher rank exact, decoder-reconstructible WRT emission
groups well enough to beat the JANUS-plus-quotient trajectory after paying an
explicit escape symbol at every active structural-role opportunity?

This is not a rescue sweep of the terminal full-vocabulary teacher. It changes
the coded object from page-tokenizer tokens to exact WRT emission groups and
changes the probability domain from the complete Gemma vocabulary to a proper
finite event alphabet with an escape branch.

## Frozen event universe

A WRT emission group contains zero or more zero-output controls followed by
the first output-producing WRT event. Groups are exact, ordered, contiguous,
and reconstruct the complete WRT stream.

Tokenize each group's decoded raw bytes independently with the frozen Gemma
tokenizer. This event-local tokenization is causal: after a group is decoded,
both encoder and decoder know its exact raw output and append the same local
token IDs to the teacher state. It does not require whole-page tokenizer
lookahead.

A group is a catalog candidate only when:

1. it contains a WRT dictionary-token event;
2. its decoded bytes are strict UTF-8;
3. event-local tokenization produces exactly one Gemma token ID; and
4. its exact `(structural_role, token_id, WRT_program)` tuple occurs in
   development.

The exact WRT program, not merely its raw surface or token ID, is the decoded
side symbol. Multiple programs sharing one Gemma token split that token's mass
with a development-frozen add-one variant distribution.

## Population

Use complete pages wholly contained in the opening raw 1M of the canonical
10M store. Split pages chronologically 60/20/20 into development, selection,
and sealed confirmation. Catalogs, escape rates, variant probabilities, and
active roles use development only and remain frozen afterward.

The teacher consumes the concatenation of event-local token IDs inside each
page. It resets to BOS every 512 local tokens. All decoded groups, including
escapes and ineligible groups, update that token context.

## Proper distributions

For role `r`, let `A_r` be the development token-ID catalog, `m_r(h)` the
teacher probability mass on `A_r`, and `epsilon_r` the Laplace-smoothed
development escape rate.

Controls:

```text
J0  exact JANUS-plus-quotient qbits on candidate WRT programs
S0  static add-one distribution over exact programs plus ESC
GF  full-mass teacher: candidate mass is native Gemma mass; ESC gets 1-m_r
GC  calibrated teacher: ESC gets epsilon_r; candidate IDs share 1-epsilon_r
```

For candidate program `v` with token ID `z`:

```text
GF(v|h,r) = P_Gemma(z|h) P(v|z,r)
GC(v|h,r) = (1-epsilon_r) P_Gemma(z|h)/m_r(h) P(v|z,r)
```

For escapes:

```text
GF(ESC|h,r) = 1-m_r(h)
GC(ESC|h,r) = epsilon_r
```

Both are normalized proper distributions. An escape retains its complete WRT
program on J0. A candidate program is omitted from J0 and charged to the named
event distribution. Every opportunity in an active role pays one side symbol;
there is no future-informed per-occurrence selector.

## Structural prerequisite

With candidate identities supplied free but the binary candidate/escape mode
entropy paid, the development ceilings are:

```text
PROSE_WORD      40,775.706 B/M
LINK_TARGET      6,721.670 B/M
LIST_ITEM        3,887.863 B/M
```

The exact static maximum-likelihood event alphabet loses 34,825.516 B/M in
prose. GC therefore has to recover more than 4.07 identity bits per prose
candidate event. This is the numeric kill condition that makes the teacher
run target-bearing rather than speculative.

## Decision procedure

1. Build catalogs and distributions from development pages only.
2. Score development with deterministic BF16 Gemma inference and FP32
   log-sum-exp.
3. Activate only roles whose development GC gain is positive and whose GC
   codelength is strictly below S0.
4. If no role activates, emit a valid `REJECT` and leave later pages unopened.
5. Score selection with the frozen catalogs and active roles. If aggregate GC
   gain is nonpositive or GC does not beat S0, reject without opening sealed.
6. Score sealed confirmation exactly once.

Promotion requires:

```text
development GC gain                  positive
selection GC gain                    positive
sealed GC gain                       >= 3,000 B/M
GC total                             < S0 total
GC total                             < GF total
event-local tokenization repeat      byte-identical
teacher calibration repeat           byte-identical
joint P1/WRT/raw alignment            exact
all probabilities                    finite, normalized, nonzero
```

A pass authorizes one finite Q24 side coder and residual arithmetic replay with
the same catalog and roles. It grants no score credit and does not authorize
distillation or native integration.

A miss retires this exact event-local tokenizer, single-token WRT program
catalog, structural roles, escape calibration, teacher checkpoint, and reset
contract without model, role, catalog, tokenizer, context, or smoothing
sweeps. The next candidate must change the event language or information
source.
