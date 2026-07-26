# REVLOG Slot-Bypass Research Plan

## Status

REVLOG is the sole authorized successor to the terminal negative
RADIX-ISLAND result. It is an oracle-only experiment and receives zero score
credit until a native, counted, deterministic codec exists.

Generic numeric extraction, STC variants, separator changes, context-key
sweeps, numeric-island extensions, and Rice-parameter sweeps remain retired.

## Hypothesis

Four outer-XML fields may contain relational redundancy absent from generic
numeric coding:

```text
/page/id
/page/revision/id
/page/revision/timestamp
/page/revision/contributor/id
```

The XML path identifies each slot without a marker. A future native codec could
code the slot through a separate REVLOG stream while replaying every original
WRT event through the parent predictor's update path. If replay is exact, the
parent state and every later non-slot probability remain identical.

## Opening Oracle

`tools/revlog_slot_bypass_oracle.py` performs the only authorized first test.
It:

1. Parses complete outer-XML pages with an exact tag stack.
2. Accepts only canonical digit IDs and canonical
   `YYYY-MM-DDThh:mm:ssZ` timestamps.
3. Maps every raw slot to whole WRT emission groups.
4. Rejects any slot that does not align exactly.
5. Attributes parent cost from the certified pre-truth endpoint P1 trace.
6. Computes a deterministic 32-bit arithmetic shadow length for diagnostics.
7. Charges explicit integer side-code, count, and finalization lengths.
8. Runs fixed seeded timestamp and username relationship controls.

The shadow arithmetic length is not an additive native archive contribution.
The integer qbit total is the primary parent information ceiling.

## Fixed Side Models

### C1: Page IDs

Strictly increasing IDs use Elias-Fano. A deterministic greedy monotone
subsequence plus explicitly enumerated exceptions handles violations. A signed
delta/Rice fallback is chosen only when its complete integer length is smaller.

### C2: Timestamps

Canonical timestamp components map injectively to a 40-bit mixed-radix scalar.
The first value is direct. Later values use one transmitted mode bit followed
by either a 40-bit direct scalar or an adaptive Rice-coded delta-of-delta.

### C3: Revision IDs

Records are stably ordered by:

```text
(decoded timestamp scalar, original page ordinal)
```

Revision IDs use the same Elias-Fano-with-exceptions versus signed-delta
decision as page IDs. `CS` deterministically shuffles timestamps before sorting
and receives no score credit.

### C4: Contributor IDs

The decoded username keys a block-local functional-dependency table. A new
username transmits its ID. An unchanged repeated username transmits no value
bits. Contradictions are carried by a predecoded enumerative exception set and
exact replacement IDs.

`CU` deterministically shuffles usernames among the same records before
applying the identical model. It is a future-informed adversarial control and
receives no score credit.

### C5: Combined

C5 combines C1 through C4, charges four 32-bit field counts and one 128-bit
side-stream finalization allowance, and compares the complete result with the
sum of exact parent qbits for disjoint selected WRT rows.

## Gates

Gate 0 requires a combined zero-bit parent ceiling of at least 4,000 B/M.

Gate 1 requires:

```text
combined fully charged gain >= 3,000 B/M
every selected class positive
C3 side bits < CS side bits
C4 side bits < CU side bits
```

Failure retires REVLOG unchanged and closes numeric research. Success freezes
all modes for identical page-complete windows near 250M, 500M, and 750M.

No native dual-range implementation is authorized until the disjoint aggregate
also clears 3,000 B/M, every retained class remains positive in aggregate, and
no individual window regresses by more than 128 B/M.

## Native Contract After All Oracle Gates

A future encoder would code selected slot values through REVLOG but still call
the ordinary parent prediction and update operations for every original WRT
bit. A future decoder would reconstruct the exact WRT events from REVLOG,
replay the same updates, and verify parent-state hashes after every field.

Required native evidence includes exact WRT and raw reconstruction, equality of
all non-slot probabilities with the parent trace, deterministic re-encoding,
complete source and framing accounting, memory, and runtime. Until those
receipts exist, REVLOG contributes zero bytes to the Hutter frontier.
