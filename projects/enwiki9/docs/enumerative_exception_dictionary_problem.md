# Independent Problem ED-1: Enumerative Exception Dictionaries

Status: `FROZEN RESEARCH PROBLEM`
Version: `ED-1`

## Definitions

Let a decoder-visible context \(c\) occur \(n_c\) times in a finite sequence.
A dictionary assigns one prototype symbol \(a_c\). Let \(e_c\) occurrences
have a different true symbol. Their ordered correctness mask is a binary word
of length \(n_c\) and Hamming weight \(e_c\).

## Questions

Prove all of the following.

1. There are exactly
   \[
   \binom{n}{e}
   \]
   binary masks of length \(n\) and weight \(e\).
2. Lexicographic ranking and unranking give a canonical bijection between these
   masks and
   \(\{0,\ldots,\binom ne-1\}\).
3. An injective fixed-length representation requires and suffices with
   \[
   \left\lceil\log_2\binom ne\right\rceil
   \]
   bits.
4. Give finite rank and unrank algorithms using Pascal binomial counts, and
   prove they are mutual inverses.
5. If contexts partition occurrences and every dictionary entry has an exact
   description cost, prove that selecting exactly the entries with positive
   omitted-cost-minus-description-minus-mask benefit maximizes total ideal
   savings.
6. Prove causal reversible decoding when the current context depends only on
   previously reconstructed symbols, the mask bit is consumed before the
   current symbol, prototype hits omit the literal, and exceptions retain it.

## Frozen application

The context is exactly the preceding four WRT bytes. For every context, the
prototype is its most frequent next byte, with smaller byte breaking ties.
Each selected entry stores:

```text
context:         4 bytes
prototype:       1 byte
occurrence count:3 bytes
exception count: 3 bytes
```

All fixed-weight masks are pooled at their exact combinatorial bit lengths and
rounded once to bytes. A four-byte dictionary-count header is charged.
Prototype hits are omitted from exact parent range replay; exceptions remain
literal.

Promotion requires exact parent payload identity, exact reconstruction, and at
least 2,000 net bytes per million raw bytes. Failure retires this exact
context-four enumerative dictionary without context-length, entry-format, or
mask-code sweeps.
