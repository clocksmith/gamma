# FCFM-1: Complete Solution

## Construction

Enumerate `Theta` in its supplied finite order. For each `theta`, compute

```text
Y_theta = E_theta(X)
Z_theta = D_theta(Y_theta).
```

Reject the member unless `Z_theta = X`. For every surviving member compute the
key

```text
K(theta) =
(
  |Y_theta| + c(theta),
  resource_rank(r(theta)),
  canonical_serialization(theta)
).
```

Return the member having the least key. If no member survives, return `FAIL`.

The algorithm terminates because `Theta` is finite and every declared
operation terminates.

## Correctness and uniqueness

Every returned member is admissible because equality is checked before
selection. The enumeration evaluates the objective of every admissible member,
so no omitted member of `Theta` can have a smaller objective. The selected
first coordinate is therefore the global minimum of `L` over the admissible
family.

The resource preorder is converted to its supplied total rank. Canonical
serializations are finite byte strings and lexicographic order on them is
total. Consequently the complete key is totally ordered. Distinct descriptions
cannot tie in every coordinate, so the selected description is unique.

## Certificate and verifier

The certificate records:

```text
SHA256(X)
SHA256(canonical Theta serialization)
for every theta:
    canonical theta
    SHA256(E_theta(X))
    |E_theta(X)|
    SHA256(D_theta(E_theta(X)))
    admissibility
selected theta
selected key
```

The verifier checks the two input commitments, reconstructs every encoder and
decoder from its canonical description, recomputes every row, rejects a
missing or duplicate family member, and recomputes the minimum key. Acceptance
proves that all declared alternatives were evaluated and that the selected row
is the global family minimum. A table containing only nearby or favorable
members is invalid because its family hash would differ.

## Closure and codec transfer

If two package members decode to the same ordered path-payload closure, they
present identical build inputs. If the frozen build additionally reproduces
the same executable and model hashes, the resulting deterministic compression
and decompression functions are identical. For every corpus input, their
archive bytes and resource behavior are then identical except for effects
explicitly excluded by the build and runtime hypotheses.

When all non-container costs agree, packages `a` and `b` satisfy

```text
Score(a) - Score(b)
  = |E_a(X)| - |E_b(X)|.
```

This identity is exact because the archive and every other counted byte agree.

## Boundary

The proof establishes optimality only over the committed finite `Theta`. It
does not claim that XZ is globally optimal, that an unlisted parameter vector
cannot improve the payload, or that the resulting compressor beats the Hutter
target. Expanding `Theta` creates a new finite problem and requires a new
certificate.

## Frozen result

The committed family contains 377 distinct XZ descriptions spanning:

1. all legal `lc/lp` pairs with `lc + lp <= 4` and `pb` from zero through four
   under the original extreme match configuration;
2. normal and fast modes, five match finders, five nice lengths, and five
   depths at `lc=4, lp=0, pb=0`;
3. a local exact refinement around the winning `bt2` region;
4. seven dictionary declarations from 768 KiB through 2 MiB.

The selected payload has parameters

```text
dict=768KiB
lc=4
lp=0
pb=0
mode=normal
nice=112
mf=bt2
depth=256
```

and length 233,000 bytes. It is 1,216 bytes smaller than the prior 234,216-byte
payload while decoding to the same 819,200-byte tar.
