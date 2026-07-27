# Problem BP-1: Fixed-Range Bucket Packing

Consider a deterministic bucketed context table with \(H=2^h\) buckets.
Every bucket stores:

- \(A\) checksums of 16 bits each;
- \(A\) state records of seven bytes each;
- one byte encoding replacement history.

The allocator stores every bucket in a cell whose byte length is a multiple of
\(q=32\). Hash reduction and bucket count must remain unchanged.

1. Prove the minimum possible cell length when no field is compressed or
   shared.
2. Compute that length for \(A=14\) and \(A=10\).
3. Prove that changing only \(A\) and the cell length preserves the bucket
   index of every lookup.
4. Give exact formulas for allocation reduction and retained entry capacity.
5. Prove that an encoder and decoder using the same deterministic replacement
   rule remain inverse stream transducers, even though their predictions may
   differ from the \(A=14\) system.
6. State precisely which compression and runtime claims still require
   execution.

## Frozen FXCM instance

The full `ContextMap2` surface contains approximately 3,841 MiB of cells.
The historical decimal-memory overage at 100M is 720,203 KiB. Determine
whether replacing 14-way, 128-byte cells by 10-way cells has enough nominal
allocation leverage to cover that overage without reducing the bucket count.
