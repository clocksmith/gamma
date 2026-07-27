# Solution to BP-1: Fixed-Range Bucket Packing

One record requires a two-byte checksum and seven state bytes, hence nine
bytes. The replacement history requires one additional byte. Any
field-preserving representation therefore needs at least

\[
9A+1
\]

bytes. With cell length constrained to a multiple of \(q\), the exact minimum
is

\[
B_q(A)=q\left\lceil\frac{9A+1}{q}\right\rceil.
\]

The lower bound follows by counting required field bytes. Rounding that count
up to the next legal multiple constructs a matching cell, so the bound is
attained.

For \(q=32\),

\[
B_{32}(14)=32\left\lceil\frac{127}{32}\right\rceil=128,
\]

and

\[
B_{32}(10)=32\left\lceil\frac{91}{32}\right\rceil=96.
\]

Keep \(H\), the hash function, and the mask \(H-1\) fixed. Then every context
hash selects exactly the same bucket before and after packing. Only the
within-bucket search and replacement set changes from 14 records to 10.

Ignoring the fixed alignment tail, allocation changes from \(128H\) to
\(96H\), an exact reduction of

\[
1-\frac{96}{128}=\frac14.
\]

Entry capacity changes from \(14H\) to \(10H\), retaining

\[
\frac{10}{14}=\frac57.
\]

For any coded prefix, both encoder and decoder have the same initial table,
observe the same previously decoded symbols, execute the same hash, search,
replacement, state transition, and probability calculation, and therefore
produce the same next-symbol probability. Induction on the coded symbols
proves exact decoder synchronization. This proves reversibility of the
deterministic construction, not equality with the 14-way archive.

On a 3,841 MiB surface, the nominal reduction is approximately 960.25 MiB,
which exceeds 720,203 KiB. The exact executable must still establish actual
RSS, archive bytes, source size, runtime, deterministic replay, and roundtrip.
