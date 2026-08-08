# Far-History Collective Ledger QM1

## Question

QM0 found 584,693 collision-verified far-history copies covering 64,526,086
raw bytes, but charged 4,058,323 canonical inline command bytes. Does the
chronological command sequence have enough collective regularity to cross the
current 4,389,323-byte target debt after paying exact positioning metadata?

## Frozen realization

The match population, anchor mask, 32-byte rolling window, 100,000,000-byte
minimum distance, 64-byte minimum length, earliest-source rule, maximal
extension, and chronological nonoverlap are copied unchanged from QM0.

For every selected command, QM1 records three canonical ULEB128 columns:

1. literal gap from the end of the previous copied target;
2. backward source distance;
3. copy length.

The header contains the record count and exact column byte lengths. A decoder
can consume each gap from the residual literal stream, copy from its already
decoded prefix, and continue. The full ledger is compressed once with Python's
deterministic LZMA preset 9 extreme. The scan and raw ledger are independently
repeated; summaries, bytes, compressed bytes, and parsed column record counts
must agree.

## Accounting and gate

Copied raw bytes retain QM0's zero-credit average-rate proxy:

```text
copied_bytes * 109,128,198 / 1,000,000,000
```

QM1 subtracts the actual compressed ledger and compressed source package.
Promotion requires at least 5,000,000 net proxy bytes, leaving more than the
4,389,323-byte debt plus a bounded reserve. Every corpus third must contribute,
and all exact/prior/closed-source proofs must pass. A pass authorizes an exact
residual-stream integration gate. It does not update the forecast or earn score
credit. A miss retires collective coding of this frozen command population
without nearby anchor, threshold, or coder sweeps.
