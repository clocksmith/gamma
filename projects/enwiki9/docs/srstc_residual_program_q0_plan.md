# SRSTC Residual-Program Retrieval Q0

Proposal: `srstc_residual_program_retrieval_q0_v1`

Status: frozen design review required. No implementation, queue entry, model
run, compression result, or score credit exists.

## Win condition

Test whether decoder-rebuilt recurrence in endpoint428's own error trajectory
can predict a fixed multi-step correction program that is absent from the
retired scalar residual tables, sparse suffix DAG, and literal-continuation
experts.

The experiment remains on the exact current endpoint428 bitstream. It does
not replace WRT, expose a new event alphabet, or select a future event length.
Its only proposed output is a sequence of bounded odds corrections to the
current parent probabilities.

Before any implementation is materialized, the exact decoder-visible
candidate universe must show at least `3,000 B/M` of oracle headroom on every
chronological split. This prerequisite follows the terminal JANUS joint-trace
recovery decision. Passing it authorizes the causal matched-control Q0 only;
it earns no score credit.

## Why this is outside the retired realizations

The retired endpoint surprise-history model maps the last `2/4/8` scalar
surprise magnitudes and current local coordinates to one current-bit mean
correction. The retired sparse context DAG maps a static completed-byte suffix
to one transmitted scalar odds correction. The typed-event realizations map
trigger/suffix/Wiki keys to point-mass literal continuations.

This proposal instead stores one fixed-length vector of quantized endpoint428
residuals and replays its aligned entries as a multi-step soft correction
program. Its primary retrieval coordinate is a summary of completed residual
programs. Completed WRT event identity and Wiki state are secondary alignment
coordinates; raw suffix and current truth are absent.

This is a different coded endpoint, not permission to tune any retired
history length, suffix depth, trigger set, continuation length, hash size,
support threshold, or blend strength.

## Exact parent and population

Bind Q0 to the committed current-parent receipts:

```text
raw opening 1M:
  bytes   1,000,000
  SHA-256 369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad

WRT store:
  bytes   600,747
  SHA-256 1e209c7d19a22af5ce6a1de3bab1fc636669f40686aebd88bbe9dc8e5411e583

endpoint428 P1:
  rows    4,805,936
  bytes   9,611,888
  SHA-256 02a263445e753604653c3cc8f7b05b783c379b0a84f576a62dd0f77438ab6715

endpoint428 archive:
  bytes   173,902
  SHA-256 6d32bddb912b14d318f2770ae2624f59d76ab402ab0fb53a13a76d4f70d6da04

endpoint428 arithmetic payload:
  bytes   173,865
  SHA-256 ab318b3c6265b4207a63290868827f9e973e03096889ac4c3333a8bf8b3911f1

page map:
  bytes   5,488
  SHA-256 3122936977eb65650601c15cd0fa42bacbbd60ad3713e18c1e99fae1e5033425
```

Use the existing `171` complete-page chronological partition:

```text
development          first 102 complete pages
selection            next 34 complete pages
sealed confirmation  final 35 complete pages
```

Model state evolves continuously across the population. Split arithmetic
counters may terminate independently for attribution, but no model, parser,
or retrieval state resets at a split.

## Exact predicted object

The text segment after the six-byte WRT header is divided into consecutive
non-overlapping `16`-byte blocks. A block boundary is decoder-visible after
the preceding byte is complete. The final partial block uses the parent and
is not inserted.

For each complete block, record the endpoint428 residual program

```text
Q = (q[0], q[1], ..., q[127]),  q[h] in {-3,-2,-1,0,1,2,3}.
```

For prior row `h`, let `p` be endpoint428's legal `P1` and `y` the already
decoded truth. Define

```text
e = (65,536 if y = 1 else 0) - p
m = min(3, floor((abs(e) + 4,096) / 8,192))
q = sign(e) * m
```

with `sign(0) = 0`. Pack each symbol in three bits. The program becomes
eligible for insertion only after all `128` truths in its block have been
decoded. Thus neither a current truth nor a future block byte enters a
prediction.

The continuation horizon is exactly `128` bits. There is no event-length
field, end marker, literal continuation, or encoder-selected action.

## Decoder-visible key

Capture the following state before the first bit of each block:

```text
residual_signature:
  simhash16 of the packed eight most recently completed residual programs

wiki_state:
  field, nesting mode, and slot rebuilt from completed raw expansions

event_prefix:
  hash8 and min(length, 7) for the already decoded prefix of the current WRT event

event_chain:
  hash16 of the four most recently completed encoded WRT events

parent_confidence:
  high nibble of endpoint428 P1 for the first block bit
```

The one frozen key language is:

```text
K0 = (0, residual_signature, field, mode)
K1 = (1, residual_signature low 8, slot, prefix length bucket, prefix hash8)
K2 = (2, residual_signature high 8, event_chain hash16, parent confidence)
```

The candidate set is the deduplicated union of `K0`, `K1`, and `K2`, ordered
by descending insertion ordinal and then program bytes. Retain at most the
eight newest programs. Require three distinct programs. There is no raw-byte
suffix hash, page identity, block identity, eventual event length, future raw
expansion, encoder-only neighbor, teacher state, or current truth.

## Bounded online state

Use one FIFO table capped at `65,536` keys and four program references per
key. A completed program is inserted under all three captured keys after its
last truth. Evict the oldest key on capacity. Duplicate program IDs across
the three keys are removed during lookup.

Prediction reads a frozen snapshot from the preceding `65,536` WRT-byte
epoch. Updates enter the live table after truth and become readable only at
the next epoch boundary. The first epoch therefore falls back completely to
the parent. The final implementation must pack the three-bit programs and
keep all added live, snapshot, parser, and index state below `256 MiB`.

The delayed snapshot is part of the algorithm, not evaluation scaffolding. It
makes every control transform deterministic, prefix-built, and reproducible
by the decoder.

## Conversion to current P1

At relative bit `h`, take the integer median of the retrieved `q[h]` values.
For an even number of values, choose the integer between the two middle
values closest to zero. Call the result `r`.

Convert `r` to an exact odds multiplier:

```text
rho(r) = (5/4)^r
```

represented as an integer numerator and denominator. For current parent
probability `p`, compute

```text
adjusted = round(
  65,536 * numerator * p
  / (numerator * p + denominator * (65,536 - p))
)
```

using unsigned 64-bit intermediates, ties upward, and final clamping to
`[1, 65,535]`. If support is below three or `r = 0`, output `p` exactly.

This defines a proper probability on the identical endpoint428 bitstream.
There is no separately coded action label. All variants observe every actual
bit, append the residual symbol after truth, and insert only a completed
program.

## Frozen variants and controls

```text
B0  exact current endpoint428 parent

F0  matched-capacity flat residual control
    Store the identical packed programs with the identical caps, epoch delay,
    and update schedule, but retrieve the eight globally newest snapshot
    programs without any semantic or residual-regime key.

R0  residual-native SRSTC
    Use K0/K1/K2, three-program support, newest-eight union, median residual,
    and the fixed 5/4 odds ladder above.

RB  support-matched blind-key control
    Preserve the R0 table and updates. In each snapshot, stratify keys by key
    family and exact resident-program count, sort their serialized key bytes,
    and redirect each lookup to the cyclic successor in its stratum. Singleton
    strata map to themselves and are counted separately. This preserves table
    size, support distribution, update frequency, and numerical machinery
    while breaking key-to-program alignment wherever a matched blind donor
    exists.

RS  shuffled-continuation control
    Preserve the exact R0 key lookup and program multiset, but read each
    program at `(h + 37) mod 128`. This preserves keys, continuation lengths,
    per-program residual-value marginals, table size, and update schedule while
    breaking temporal continuation alignment.
```

R0 must beat B0, F0, RB, and RS. A win against only a weak or misaligned
control is not promotable.

## Gate minus one: new-information ceiling

Before materializing R0, enumerate only the programs available from the
causal preceding-epoch snapshot. For each current 16-byte block, an oracle may
choose B0 or one complete candidate program after seeing that block's truths.
Charge a four-bit candidate index for the nine-way B0-plus-eight universe and
exact arithmetic termination. The oracle choice is noncausal and receives
zero credit; the candidate universe
and all stored programs are causal.

Require at least `3,000 B/M` gross headroom independently on development,
selection, and sealed confirmation. Failure retires this proposal before
implementation. Passing authorizes only the exact causal Q0 below.

## Same-stream exactness contract

Require all of the following:

```text
input P1 hash and row count                 exact
B0 arithmetic payload                      byte-identical to 173,865-byte parent payload
B0/F0/R0/RB/RS predicted stream            identical endpoint428 truth stream
prediction                                 before current truth
residual observation                       after current truth
program insertion                          after complete 128-bit program
snapshot visibility                        preceding epoch only
all five arithmetic decodes                exact
WRT reconstruction                         exact
official WRT-to-raw inverse                 exact
second R0 state, P1, and payload            byte-identical
all probabilities                          legal and nonzero
```

Any violation terminates the realization as invalid evidence.

## Frozen economics

The Q0 package charge is:

```text
actual compressed canonical decoder/model source delta
+ actual framing and termination
+ any transmitted retrieval structure
```

The table is rebuilt online, so it has no invented payload charge. Its source,
runtime, and measured memory are not free. Until native source exists, reserve
`131,072` program bytes plus `64` framing bytes and require the eventual
actual complete delta not to exceed that reserve.

Promotion from opening 1M to one unchanged distant 1M requires:

```text
R0 gross sealed gain                         >= 3,000 B/M
R0 package-adjusted projected gain           >= 2,100 B/M
development gain                             positive
selection gain                               positive
sealed-confirmation gain                     positive
R0 payload                                   < B0 payload
R0 payload                                   < F0 payload
R0 payload                                   < RB payload
R0 payload                                   < RS payload
complete added package                       <= 131,136 bytes
added decoder state                          <= 256 MiB
all exactness conditions                     pass
```

Projected package adjustment amortizes the complete added bytes across the
canonical `1,000,000,000`-byte scope. No archive gain, source allowance, or
oracle headroom changes the current forecast until an exact native counted
receipt exists.

The distant 1M must use the exact frozen implementation and independently
clear the same `3,000 B/M` gross and `2,100 B/M` package-adjusted floors. Only
then may one exact native 10M integration be proposed.

The governing native inequality remains:

```text
archive gain at 1G
  > 1,389,323
    + actual source-package delta
    + actual framing delta
    + safety reserve
```

## One-shot retirement rule

Any valid miss retires exactly this:

```text
16-byte / 128-bit non-overlapping program horizon
three-bit residual quantization at 8,192-unit steps
eight-program residual signature
K0/K1/K2 key language
65,536-key FIFO cap
four program references per key
three-program support floor
newest-eight candidate rule
65,536-WRT-byte delayed snapshot
integer median routing
fixed 5/4 odds ladder
37-position shuffled-program control
```

Do not sweep block length, signature width, key composition, hash size, table
cap, programs per key, support, candidate count, epoch size, quantization,
odds strength, or shuffle rotation after seeing sealed results. A successor
must introduce a materially different information source or coded endpoint.

## Artifact and execution gate

The original and minified endpoint428 parent packages were recovered and
identity-verified on `/home/x`; they are not currently materialized on this
host. The committed receipts are sufficient for provenance and canonical
accounting, but not for this replay.

Before Gate minus one or Q0 can run here, transfer and hash-check:

```text
280,147-byte source package     19ddcc4ec1b6f31958bed4aa19c0fbc83a56c78121933e1447e4ee011547aee0
261,125-byte minified package   b6fe6b09d6adbd8a287a08d284ca1f439ba72ff007b4d40c66bf7647a54a5d43
comp9a-decomp9                  37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361
cmix.bin                        d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194
english.dic                     4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a
current-parent 1M P1            02a263445e753604653c3cc8f7b05b783c379b0a84f576a62dd0f77438ab6715
current-parent WRT store        1e209c7d19a22af5ce6a1de3bab1fc636669f40686aebd88bbe9dc8e5411e583
page map                        3122936977eb65650601c15cd0fa42bacbbd60ad3713e18c1e99fae1e5033425
parent trace decision           d43da82a3d843eb6e584342a35e252555074e7888402973f826f692cb761a3e7
```

No execution is authorized by this design document. Review approval and local
artifact materialization are both required before an oracle tool, candidate
program, or queue entry is created.

## Claim boundary

```text
candidate:          srstc_residual_program_retrieval_q0_v1
status:             frozen design review required
mathematics:        same-stream causal construction specified
compression result: unmeasured
source status:      no implementation
score credit:       0
full-corpus claim:  none
```

The exact JANUS joint P1 recovery remains observation-only and terminal as a
codec. This proposal does not reopen JANUS, typed-event point masses, sparse
suffix DAGs, LOGOS, NOEMA, or the older Atlas-Clockwork problem bank.
