# NNCP Post-Preprocessor Aligned Copy QM0

## Question

The published NNCP v3.3 total is 107,261,318 bytes, 2,261,318 above the current
105M objective. Its exact full-corpus preprocessor receipt contains 200,608,961
16-bit symbols and reconstructs canonical enwiki9. Does this coded alphabet
retain enough exact sequence repetition outside NNCP's direct 256-symbol
memory plus 64-symbol segment to close that debt with paid copies?

## Frozen scanner

The input is the receipt-bound 401,217,922-byte `preprocessed.bin`, SHA-256
`c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5`.
It contains exactly 200,608,961 little-endian 16-bit symbols.

The content-defined scanner uses a 32-byte window, low-six-bit anchor, two
independent 64-bit hashes, exact comparison before extension, 640-byte minimum
distance, 64-byte minimum length, earliest source, maximal extension, and
chronological nonoverlap. Anchors, backward/forward extension, gaps, distances,
and lengths remain two-byte aligned. Every source is prior and fully closed.

Commands are columnar canonical ULEB128 gap, distance, and length values. Two
fresh scans must produce identical summaries, raw ledgers, compressed ledgers,
and valid aligned command replays.

## Gate

Copied serialized-symbol bytes are priced at the published NNCP archive rate
`106,632,363 / 401,217,922`. The actual compressed ledger and a fixed 65,536
byte integration allowance are subtracted. Promotion requires at least 40M
copied bytes, 4M net archive-rate-equivalent bytes, and positive coverage in
all thirds. This exceeds the 2,261,318 score debt plus integration and transfer
reserve.

A pass authorizes only a separately frozen NNCP residual integration: neural
decode must reconstruct the residual symbols, the copy inverse must reproduce
the exact preprocessed stream, and the existing dictionary inverse must restore
canonical enwiki9. The native gate must account for changed online training,
actual archive bytes, program/ledger bytes, deterministic replay, memory, and
runtime. QM0 is external-parent average-rate evidence with zero score credit.
