# Factoradic Recency Tie-Breaking

## Independent finite problem FRT-1

Let \(A\ge 1\), let \(W=\{0,\ldots,A-1\}\), and let a recency state be a
permutation \(\pi\in S_A\), ordered from most recently used to least recently
used. Every access names one way \(j\in W\).

1. Construct canonical mutually inverse maps
   \[
   \operatorname{rank}:S_A\to\{0,\ldots,A!-1\},\qquad
   \operatorname{unrank}:\{0,\ldots,A!-1\}\to S_A
   \]
   using Lehmer digits and lexicographic order.
2. Prove that exactly \(\lceil\log_2(A!)\rceil\) bits are necessary and
   sufficient for a fixed-width representation of every recency order.
3. Define the move-to-front transition after an access and prove that rank,
   transition, and unrank form a deterministic finite-state machine.
4. Given priorities \(p_0,\ldots,p_{A-1}\), define the eligible set
   \[
   M=\{j:p_j=\min_i p_i\}.
   \]
   Construct the canonical way in \(M\) that is least recently used. Prove
   that the rule never replaces a nonminimum-priority way.
5. Prove that position \(r\) in \(\pi\) means exactly \(r\) distinct ways
   have been accessed more recently since the last access to that way, subject
   to the fixed initial order for ways never yet accessed.
6. Give exact operation bounds for direct rank, unrank, move-to-front, and
   minimum-priority/LRU selection.
7. Specialize to \(A=10\). Determine the minimum bit width and show whether a
   32-bit field fits in the unused tail of the frozen 96-byte FXCM cell whose
   fields are ten 16-bit checksums, one byte, and ten seven-byte states.
8. State a finite implementation certificate and the exact enwiki9 transfer
   boundary.

All way orders, integer encodings, and ties are frozen. This problem concerns
finite permutations and deterministic state machines; it assumes no corpus.

## Organizer-owned transfer reduction

The B2 FXCM layout uses ten ways and a 96-byte cell. Its prior logical fields
end at byte 91 and occupy 92 bytes after two-byte alignment. FRT-1 may add one
32-bit factoradic recency rank at offset 92 without changing the 96-byte cell,
bucket count, hash reduction, fingerprints, predictor states, or priority
rule. On a miss, it may choose the least-recent way only among ways tied for
minimum existing priority. Encoder and decoder update the rank after the same
hit or replacement.

The theorem licenses this exact representation and synchronization argument.
It proves no compression gain. Native promotion requires package accounting,
exact roundtrip, deterministic replay, decimal-memory compliance, and positive
joint archive economics on frozen opening and distant gates.
