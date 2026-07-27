# Bootstrap Prefix Dictionary Problem

Status: independent constructive problem
Version: `BPD-1`

This problem is independent of the Atlas-Clockwork problem banks. It concerns
finite strings, deterministic dictionaries, and reversible compositions. No
compression claim is assumed.

## Given

Let \(X\) be a finite byte string and let \(m,K\) be nonnegative integers.
Write

\[
P=X[0:\min(m,|X|)],\qquad S=X[|P|:|X|].
\]

Define a token of \(P\) to be a maximal nonempty interval of ASCII letters.
Normalize each token by mapping `A` through `Z` to `a` through `z`. For each
distinct normalized token \(w\), let \(f(w)\) be its frequency and \(a(w)\)
the starting offset of its first occurrence.

Order tokens by

\[
(-f(w),a(w),w)
\]

using bytewise lexicographic order in the final coordinate. Let \(L_K(P)\) be
the first \(K\) ordered tokens, serialized as one token plus newline per entry.

For every finite dictionary \(D\), suppose deterministic maps

\[
E_D:\{0,\ldots,255\}^*\to\{0,\ldots,255\}^*,
\qquad
R_D:\{0,\ldots,255\}^*\to\{0,\ldots,255\}^*
\]

satisfy \(R_D(E_D(Y))=Y\). Let \(E_\bot,R_\bot\) be a deterministic
dictionary-free pair with the same property.

The archive contains a fixed magic string, the four integers

\[
|X|,\ |P|,\ |E_\bot(P)|,\ |E_{L_K(P)}(S)|,
\]

in fixed-width big-endian form, followed by the two payloads in that order.

## Questions

1. Prove that \(L_K\) is finite, deterministic, and invariant under any
   encoder implementation that obeys the stated byte rules.
2. Construct the decoder and prove exact reconstruction for every finite
   \(X,m,K\), including empty prefix, empty suffix, and empty dictionary.
3. Prove deterministic second-archive identity when both component encoders
   are deterministic.
4. Give exact archive and package accounting. If a static dictionary of
   package length \(d\) is removed and code growth is \(c\), prove the new
   construction wins exactly when

   \[
   |A_{\rm new}|-|A_{\rm old}|<d-c.
   \]

5. Prove causality: every dictionary byte used to decode the suffix is a
   deterministic function of bytes decoded before the suffix.
6. Give a canonical finite verifier for the token order, dictionary bytes,
   frame, reconstruction, and deterministic re-encoding.

