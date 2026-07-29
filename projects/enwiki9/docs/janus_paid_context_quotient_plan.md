# JANUS-QUOTIENT Q0: Paid Fixed-Population Context Quotient

Status: PREDECLARED / ZERO SCORE CREDIT

## Question

Can a compact, explicitly transmitted quotient of decoder-visible endpoint428
history retain enough fixed-corpus residual information to pay at target scale?

This is the only authorized successor to the terminal CHIRON-shaped JANUS
recurrent witness. It changes the model family rather than its width, training
schedule, optimizer, reset length, or precision.

## Frozen model

The model contains exactly 65,536 states. Before each WRT bit, its state is a
fixed hash of:

- the previous four completed WRT bytes;
- the current byte-tree node, including bit position and decoded prefix;
- a 32-bin quantization of the exact parent P1.

Every state stores one byte selecting one of seven rational odds multipliers:

```text
1/4, 1/2, 2/3, 1, 3/2, 2, 4
```

The eighth code is reserved as identity. There is no architecture, state-count,
hash, correction-alphabet, or training sweep.

The complete canonical `JQDG1` model is transmitted and counted. The ledger is:

```text
compressed canonical model blob
+ 24,576-byte native decoder allowance
+ 64 framing bytes
```

The complete oracle harness is reported separately and receives no decoder
credit.

## Training and runtime causality

Q0 fits each state's correction on the same fixed 10M population that it
encodes. This is legal two-part coding: the fitted state table is transmitted
before the arithmetic payload and every model byte is charged.

At runtime, the decoder uses only the transmitted table, the exact parent P1,
and already decoded WRT bytes and bit prefixes. No teacher state, future bit,
block identity, or untransmitted label is available.

## Exact controls

```text
J0  exact source-bound endpoint428 parent payload
JQ  paid 65,536-state context quotient
JS  identical paid table circularly shifted by 8,191 states
```

The shifted control preserves the correction-code population while breaking
its association with the causal quotient state.

Two complete fits must produce identical tables, canonical blobs, adjusted P1
streams, and arithmetic payloads. J0 must reproduce the receipt-bound parent
payload byte for byte. JQ and JS must decode the complete WRT stream, whose
existing exact inverse receipt binds reconstruction to the raw 10M input.

## Authorization

Authorize a larger constructive successor only when all conditions hold:

```text
gross exact gain                 >= 3,000 B/M
package-adjusted projected gain  >= 2,100 B/M
JQ payload strictly smaller than JS
complete package                 <= 128 KiB
parent payload identity          exact
JQ and JS arithmetic decode      exact
WRT/raw inverse receipt          bound
A/B model, P1, and payload        identical
```

A valid rejection exits successfully and records zero score credit. Failure
retires this exact paid quotient, its hash, its state count, and its correction
alphabet. It does not prove that every transmitted fixed-corpus model is
subeconomic.

