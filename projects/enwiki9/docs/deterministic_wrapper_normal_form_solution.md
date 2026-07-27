# DWNF-1: Complete Solution

## Alpha-equivalence

For private roots `R` and `R'`, define `R/u` and `R'/u` to correspond for every
relative path `u`. Extend this relation to wrapper states by requiring equal
source-member bytes, equal cached executable bytes, equal model bytes, equal
input and output bytes, and corresponding private paths. Host paths outside
the private roots must agree literally.

## Transition semantics

Wrapper states contain:

```text
source closure
optional build root
optional executable and model
effective environment
runtime argument vector
input bytes
output bytes
```

Extraction maps every closure member `(u, x)` to `R/u = x`. Build maps the
extracted closure and effective flags to executable and model bytes. A cache
hit returns those same bytes. Run consumes executable bytes, model bytes,
arguments, environment, and input bytes and produces output bytes. Read
returns those bytes as the sole observation.

## Bisimulation

Relate the initial states of `W` and `W'`. Identical closures make extraction
steps correspond under the root alpha-map. Identical effective build flags and
deterministic build semantics produce equal executable and model bytes; the
frozen hashes check this obligation. Cache hits preserve the relation.

Both wrappers prepend their corresponding private root to the same prior
`LD_LIBRARY_PATH`, so their environments agree after root alpha-renaming.
Their runtime arguments and input bytes agree literally. Path-alpha invariance
and deterministic process semantics therefore produce equal output bytes.
Reading those bytes preserves the relation and yields equal observations.

Induction over the finite transition trace proves:

```text
compress_W(x) = compress_W'(x)
decompress_W(y) = decompress_W'(y)
```

for every input on which the hypotheses hold.

Fresh prefix spelling is unobservable because every occurrence is transformed
by the same root alpha-map. Comments and type annotations do not participate
in Python runtime transitions here. Eliminating a local name is valid when its
defining expression is evaluated at the same transition and every use receives
the same value. Combining deterministic statements on one physical line does
not change their execution order.

## Certificate

The frozen certificate contains:

```text
source-package hash
effective build flags
parent and child executable hashes
parent and child model hashes
effective compression arguments
effective decompression arguments
environment-construction rule
wrapper byte lengths and hashes
native archive and roundtrip receipts
```

A verifier rebuilds both closures, checks the hashes and effective labels, and
then performs native archive equality and roundtrip tests. Static equivalence
without the native test is a source-transfer certificate, not score evidence.

## Score transfer

If both wrappers emit the same archive and all other package members agree,
then

```text
Score(W) - Score(W') = |source(W)| - |source(W')|.
```

For the frozen instance:

```text
2294 - 1099 = 1195 bytes.
```

The normal form therefore saves exactly 1,195 counted package bytes
conditional on native archive identity.
