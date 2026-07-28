# CHIRON Frozen Residual LM Plan

Status: terminal rejection

Score credit: zero until a deterministic integer decoder is integrated and exact
native replay passes.

## Question

Can a compact frozen causal model predict a target-scale portion of the exact
endpoint428 residual error that was not captured by static hashes, paid page
labels, component routing, or the online compact-NNCP startup experiment?

CHIRON is not an autonomous replacement predictor. It receives the exact
endpoint428 probability for each coded bit and emits a bounded logit correction.
It is trained offline on chronological data, frozen, and evaluated using only
already decoded WRT bytes.

## Fixed Q0 architecture

The first and only Q0 architecture is:

```text
alphabet                 256 WRT bytes plus BOS
causal block             256 completed WRT bytes
state reset              every 256 WRT bytes
embedding width          64
GRU hidden width         96
GRU layers               2
readout                  255 binary-prefix nodes
training epochs          8
parameter quantization   signed int8 per tensor
```

For byte position `t` in a block, the model consumes byte `t-1`, or BOS when
`t=0`. Its state therefore depends only on completed bytes. The 255 outputs
correspond to nodes in the depth-eight binary byte tree:

```text
node(bit_position, decoded_prefix)
    = (1 << bit_position) - 1 + decoded_prefix
```

The chosen node correction is added to the exact endpoint428 logit. Endpoint428
state and probabilities are not changed.

Offline training may use batched blocks because block resets are part of the
declared decoder. Holdout replay must use the identical reset and input schedule.

## Population

Use the receipt-bound opening-1M endpoint trace:

```text
/home/x/enwiki9-nonproof/results/endpoint428_pair_layer0_online_native_1m_v1/native.p1
/home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin
```

The complete fixed blocks are divided chronologically:

```text
training     first 70%
development next 15%
holdout      final 15%
```

No model, optimizer, quantizer, threshold, or architecture choice may change
after inspecting holdout.

## Controls

```text
C0  exact endpoint428 p1
C1  one trained scalar residual per binary-prefix node
C2  quantized CHIRON residual
CS  C2 residuals circularly shifted by 4093 WRT bytes
```

The trace is valid only if C0 reproduces the exact recorded parent payload for
the complete trace.

## Accounting

Report exact range-coded bytes on development and holdout. Convert holdout gain
to bytes per million raw bytes using the receipt-bound WRT/raw ratio.

The provisional package charge is:

```text
compressed int8 tensor certificate
+ compressed oracle source
```

This charge is an oracle screen, not final submission accounting.

## Authorization gate

Authorize a constructive integer Q1 only when all conditions hold:

```text
C2 holdout gross gain             >= 3,000 B/M
C2 holdout net gain               >= 2,100 B/M
C2 exact gain                     > C1 exact gain
C2 exact gain                     > CS exact gain
C2 development exact gain         > 0
complete C0 trace replay          exact
```

If the gate fails, reject the frozen residual neural lane unchanged. Do not run
a width, depth, context, precision, optimizer, or epoch sweep.

## What a positive Q0 would authorize

A positive Q0 authorizes one deterministic integer implementation with explicit
GRU accumulation, activation tables, probability quantization, model
serialization, roundtrip, deterministic re-encode, package accounting, memory,
and runtime receipts. Q0 itself receives no forecast or score credit.

## What a negative Q0 closes

A negative Q0 closes compact frozen recurrent correction trained directly on
endpoint428 residuals at this information scale. It does not reopen online NNCP,
LibNC reproduction, page prompts, component routing, static residual hashes, or
teacher-hidden-state transfer.

## Terminal result

Job `20260728T185712Z_43dab2487d` completed the fixed Q0 experiment.

```text
complete parent replay          173,859 bytes, exact
development baseline             25,593 bytes
development CHIRON               25,602 bytes
development gain                     -9 bytes
holdout baseline                 23,417 bytes
holdout CHIRON                   23,424 bytes
holdout gain                         -7 bytes
node-bias holdout gain              -61 bytes
shift-null holdout gain             -46 bytes
gross holdout rate               -46.534 B/M
provisional package             147,056 bytes
net holdout rate                -193.590 B/M
```

The exact parent identity gate passed. Development, gross-rate, and net-rate
gates failed. CHIRON is rejected with zero score credit. Q1 is not authorized,
and no architecture or training sweep is permitted.
