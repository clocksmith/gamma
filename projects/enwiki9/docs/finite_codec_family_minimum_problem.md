# FCFM-1: Finite Codec-Family Minimum

## Given

Let `X` be a finite byte string and let

```text
Theta = (theta_1, ..., theta_m)
```

be a finite totally ordered list of codec descriptions. For every `theta`:

1. `E_theta` is a deterministic encoder;
2. `D_theta` is a deterministic decoder;
3. `c(theta)` is a nonnegative counted fixed cost;
4. `r(theta)` is a nonnegative resource vector;
5. every operation has finite exact semantics.

An admissible description satisfies

```text
D_theta(E_theta(X)) = X.
```

Define

```text
L(theta) = |E_theta(X)| + c(theta).
```

Resource vectors are ordered by a supplied total preorder `<=_R`. Codec
descriptions have a canonical finite serialization.

## Questions

1. Construct a finite algorithm that returns an admissible `theta*` minimizing
   `L(theta)` over all of `Theta`.
2. Among equal-length minimizers, require minimum resource rank and then the
   lexicographically first canonical serialization. Prove uniqueness.
3. Construct a certificate containing the hash of `X`, the ordered family,
   every encoded length and hash, every decoded hash, and the selected member.
   Give a deterministic verifier.
4. Prove that the verifier establishes global, not local, optimality over the
   declared family.
5. Suppose every admissible member decodes to an identical finite source
   closure and all selected builds reproduce fixed executable and model hashes.
   Prove exact codec-function transfer.
6. Derive the exact counted package difference between two members when their
   non-container fixed costs agree.
7. State precisely what the result does not prove about codec descriptions
   outside `Theta`.

## Frozen enwiki9 instance

`X` is the canonical 819,200-byte Compact5 NNCP source tar. `Theta` is the
finite XZ family serialized by
`tools/finite_xz_family_minimum.py`. All members use one x86 filter followed by
one LZMA2 filter. The objective is compressed payload length, then declared
dictionary bytes, then canonical parameter text.

The theorem receives no Hutter score credit by itself. Native archive,
roundtrip, determinism, runtime, memory, and complete package accounting remain
mandatory.
