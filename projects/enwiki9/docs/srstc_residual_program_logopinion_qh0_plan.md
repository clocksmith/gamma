# SRSTC residual-program log-opinion consensus QH0

Proposal: `srstc_residual_program_logopinion_v1`

Candidate: `srstc_residual_program_logopinion_qh0_v1`

Status: frozen zero-credit causal ceiling. No compression result or forecast
credit exists.

## Claim boundary

The terminal residual-program selector gate found real pre-selector
information but insufficient command economics. Its exact residual payload
saved `3,026 B/M` on development, `4,581 B/M` on selection, and `4,784 B/M`
on sealed pages before the frozen four-bit selector. The selector then made all
three populations strongly negative.

This successor removes the per-block command. It does not choose a prior
program after seeing the current block and does not transmit a candidate
index. Instead, all causally retrieved programs contribute to one deterministic
current-bit odds correction.

## Frozen information source

Reuse only the causal program observations needed to test the new operation:

- consecutive complete 16-byte WRT blocks after the six-byte segment header;
- 128 residual symbols in `[-3, 3]`, quantized at 8,192 P1 units and packed in
  three bits;
- eight-program residual SimHash;
- K0/K1/K2 decoder-visible keys;
- 65,536-key FIFO live table with four references per key;
- 65,536-WRT-byte preceding-epoch snapshots;
- at most the eight newest distinct retrieved programs and support at least
  three.

The current block, current truth, eventual event length, future raw expansion,
and encoder-only neighbors remain excluded. A program is inserted only after
all 128 of its truth bits have been decoded. A snapshot may expose only
programs complete at or before its epoch boundary.

## New coding operation

For relative bit `h`, let the retrieved residual symbols be

```text
q_1[h], ..., q_n[h], n in [3, 8].
```

The log-opinion consensus exponent is

```text
r[h] = trunc_toward_zero((q_1[h] + ... + q_n[h]) / n).
```

If `r[h] = 0`, emit the exact endpoint428 P1. Otherwise multiply the parent
odds by `(5/4)^r` using the same unsigned-64-bit rational arithmetic, nearest
integer with ties upward, and clamp to `[1, 65,535]`.

This is the geometric mean of the candidate odds multipliers projected back
onto the frozen integer exponent alphabet. It has no action symbol, index
stream, event framing, or future-informed decision. Every decoded truth still
updates the ordinary parent trajectory and the residual-program observer.

## Controls

```text
B0  exact endpoint428 parent

F0  flat consensus
    Use the eight globally newest distinct programs visible in the same
    preceding-epoch snapshot, with identical support and log-opinion math.

R0  keyed log-opinion consensus
    Use the K0/K1/K2 deduplicated newest-eight candidate union.

RB  support-matched blind keys
    At each snapshot, redirect each key to the next serialized key in the
    same key-family and exact resident-reference-count stratum. Singleton
    strata map to themselves and are reported separately.

RS  rotated programs
    Use the exact R0 candidates but read q[(h + 37) mod 128].
```

R0 must beat B0, F0, RB, and RS. There is no post-result selector, strength,
support, or consensus-rule sweep.

## Exact population and gates

Use the receipt-bound opening-1M endpoint428 P1, WRT store, raw input,
dictionary, archive, and 171-page map. State remains continuous. Attribution
uses the frozen 102/34/35 development, selection, and sealed page split.

Require:

```text
parent payload identity                     exact
all five arithmetic decodes                 exact
complete WRT reconstruction                 exact
official raw inverse                        exact
second R0 state, P1, and payload             byte-identical
all probabilities                           legal and nonzero
all retrieved programs                      preceding-epoch causal

development R0 gain                         positive
selection R0 gain                           positive
sealed R0 gain                              >= 3,000 B/M
full R0 gain                                >= 3,000 B/M
R0 payload                                  < F0 payload
R0 payload                                  < RB payload
R0 payload                                  < RS payload
```

QH0 temporarily supplies the observer implementation and online tables for
free. Actual residual arithmetic and termination are exact. A pass authorizes
only a paid source/model allowance gate requiring at least `2,100 B/M` after
the complete package. It does not alter the forecast or authorize native 10M.

## One-shot retirement

A valid miss retires this componentwise mean log-opinion operation over this
causal residual-program source. Do not sweep mean versus median, support,
candidate count, exponent scale, odds base, signature, table size, epoch,
rotation, or key language. A successor must change the information source or
the coded representation again.

Forecast remains `109,389,323` bytes, target debt remains `1,389,323`, score
credit is zero, and verified full-1G remains unknown.
