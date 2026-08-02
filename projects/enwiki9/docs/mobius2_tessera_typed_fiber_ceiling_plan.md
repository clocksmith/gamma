# MÖBIUS-2 TESSERA Typed Fiber Ceiling QH0

Proposal: `mobius2_tessera_typed_fiber_ceiling_v1`

Candidate: `mobius2_tessera_typed_fiber_ceiling_qh0_v1`

TESSERA is a state-preserving typed lexical event side-stream. It does not
adjust JANUS-plus-quotient logits. It reconstructs selected complete WRT token
events from a finite side alphabet, removes their truth bits from the residual
arithmetic stream, and advances over the corresponding fixed P1 rows exactly
as a later native decoder would update all parent state with the reconstructed
bits.

The primary reference is the exact canonical opening-10M JANUS recurrent plus
paid quotient trajectory. Endpoint428 is an overlap diagnostic only. Neither
retired model receives forecast credit.

## Frozen input bindings

```text
joint P1:
  results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1

joint payload:
  results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload

endpoint428 P1 and archive:
  results/endpoint428_pair_layer0_online_native_trace_10m_v1/native.p1
  results/endpoint428_pair_layer0_online_native_trace_10m_v1/archive.bin

WRT truth:
  results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin

raw input:
  data/enwik9_10000000.bin

dictionary:
  /home/x/enwiki9-nonproof/results/
  cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/
  clean-build-b/build/english.dic
```

The joint trace-recovery decision, joint decision, endpoint trace decision,
and official WRT inverse receipt are mandatory hash bindings.

## Exact event universe

One eligible lexical event is one complete WRT dictionary-token event emitted
by `tools/wrt_exact.py`. Literal runs, controls, escapes, segment headers, and
partial token codes are never silently grouped. A typed record identifies the
canonical lowercase decoded lexeme, morphology, surface class, and exact WRT
encoded variant; the latter makes reconstruction byte-exact.

At every WRT event boundary, a role is computed from raw bytes decoded before
that event. The frozen role alphabet is:

```text
OUTSIDE PAGE_TITLE SECTION_HEADING PROSE_WORD LINK_TARGET LINK_LABEL
TEMPLATE_NAME TEMPLATE_KEY TEMPLATE_VALUE CATEGORY REFERENCE_FIELD URL
DATE NUMBER MEASUREMENT TABLE_CELL LIST_ITEM
```

An active role routes every event opportunity through the side coder. A known
token uses a typed record. Every other event emits an explicit `ESCAPE` and is
decoded from the residual JANUS-plus-quotient stream. Thus the gate has no
per-occurrence future-informed selector. Inactive roles use residual coding
without a side symbol.

## Corpus-induced semantic graph

Only complete development pages contribute model counts. Deterministic raw
parsers extract page titles, link targets and labels, template names and keys,
categories, headings, reference fields, lead text, title/lead overlap, and
number/date/unit/URL shapes. These relations define each lexeme's initial
self-annotation signature.

Initial signature groups are merged by one deterministic agglomerative MDL
procedure. Its objective is the frozen 1/256-bit static side-symbol length plus
an eight-byte provisional type-record charge. Only types with overlapping
structural-role support are legal merge pairs. Apply the largest strictly
positive saving, break exact ties by ascending type IDs, retain the smaller ID,
and stop when no merge saves one qbit. There is no requested type count or
merge threshold.

The shuffled control rotates type assignments once within exact bins of
development frequency bucket, WRT encoded length, morphology, surface class,
role-support count, and dictionary status.

## Static finite side coder

The Q24 side coder uses a 32-bit integer range and largest-remainder frequency
projection. Every legal symbol has a nonzero frequency and each CDF totals
`2^24`. Equal remainders break by ascending symbol ID. Coder termination is an
actual finite byte string.

The event factorization is:

```text
TAG(ESCAPE | TYPED)
TYPE
LEXEME
MORPHOLOGY
SURFACE
EXACT_WRT_VARIANT
```

F1 and F2 retain the one-symbol collapsed TYPE field so framing and operation
order remain matched. The side archive pays magic, schema, variant ID, raw/WRT
lengths, residual length, side length, active-role mask, and termination.

## Split discipline

Complete pages are chronological:

```text
development          first 60%
selection            next 20%
sealed confirmation  final 20%
```

Development builds the graph and static count tables. Selection chooses the
active F3 role fibers by aggregate 1/256-bit economics. A role is active only
when all its selection occurrences together have strictly positive displaced
joint qbits after every F3 side symbol. The active set is then frozen and used
unchanged for all controls and sealed confirmation. No event-level choice is
made from true codelength.

Independently terminated split streams are diagnostics. One complete-stream
archive supplies the identity certificate.

## Frozen controls

```text
F0  exact JANUS-plus-quotient parent replay
F1  one global untyped lexeme dictionary
F2  role-conditioned lexeme/morphology/surface fiber; semantic TYPE collapsed
F3  full corpus-induced semantic types
FR  frequency/length/shape/morphology/support-matched shuffled type assignment
```

The identical active roles and event boundaries apply to F1, F2, F3, and FR.
The same F3 side operations are also run against endpoint428 solely to report
`G_E` and `eta_orthogonal = G_J / G_E`.

## QH0 accounting and gate

Temporarily free:

```text
type graph and lexeme mapping
static frequency tables
decoder/source implementation
```

Paid exactly:

```text
TAG, TYPE, LEXEME, MORPHOLOGY, SURFACE, and variant symbols
ESCAPE symbols
side-stream framing and termination
remaining residual arithmetic bits and termination
```

The canonical provisional model is serialized twice and compressed only for a
diagnostic size. It is not charged at QH0 and earns no score credit.

Authorization requires:

```text
joint and endpoint parent payload identity       exact
side and residual decode                          exact
complete WRT reconstruction                       exact
official raw inverse                              exact
second model/side/residual build                   byte-identical
all Q24 CDFs                                       legal and nonzero
development, selection, sealed F3 gain             positive
F3 incremental 10M gain over joint                 >= 30,000 bytes
F3 total                                           < F1, F2, and FR totals
```

`REJECT` is a successful process result. Nonzero exit denotes broken evidence.
A miss retires this exact graph, factorization, merge objective, alphabet, event
universe, and all enumerated rescue sweeps. A pass authorizes only a paid TSF1
model gate requiring at least 2,100 package-adjusted B/M.

The forecast remains 109,389,323 bytes and the verified full-1G score remains
unknown until a counted native codec exists.
