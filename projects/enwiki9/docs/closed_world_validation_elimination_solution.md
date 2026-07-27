# Solution: Closed-World Validation Elimination

## Closed-world relation

Fix the unique packaged object \(A\). Relate a parent state immediately before
a validation predicate to the child state immediately before the next
successful-path operation. Require all ordinary variables, extracted bytes,
private paths up to alpha-renaming, build labels, external inputs, and outputs
to agree.

Every \(P_i(A)\) is true and pure. The parent evaluates it, takes the success
edge, and changes no observable state. The child takes zero steps and remains
related to the parent's successor. This is a stuttering bisimulation.

Between validations, both wrappers execute identical successful-path
operations. Induction over the finite trace proves identical extracted
members, restored auxiliary data, effective build labels, executable bytes,
runtime arguments, and output bytes.

## Certified structural checks

Bounds and path checks can be removed under the same argument when a finite
certificate establishes, for every record:

1. header and payload endpoints lie within \(A\);
2. the final cursor equals \(|A|\);
3. paths are nonempty, relative, contain no `..`, and are unique;
4. BPDQ records are nonempty;
5. every prefix length lies between zero and the prior word length.

The certificate evaluates the same relations once against the immutable object
hash. The submitted wrapper need not reevaluate them on every construction.

The theorem does not apply if \(A\) is mutable, selected by a user, downloaded
at runtime, or replaced without changing the package certificate. It does not
apply to corpus bytes, compressed archive bytes, arithmetic-decoder state, or
roundtrip output. Checks over those external values remain semantically live.

## Certificate and score transfer

The finite certificate contains:

1. \(A\)'s bytes, length, and hash;
2. the complete predicate list;
3. every predicate result and structural witness;
4. parent and child successful-path transition labels;
5. parent and child wrapper bytes and hashes;
6. restored executable and auxiliary-data hashes;
7. native archive and roundtrip receipts.

If parent and child archives and all other package members agree, then

\[
\operatorname{Score}(W)-\operatorname{Score}(W')
=|W|-|W'|.
\]

Static validation elimination and restored-runtime identity are constructive
package evidence only. Exact native archive identity, roundtrip, deterministic
second archive, runtime, memory, and full score remain mandatory.

## Frozen B2 result

The immutable closure certificate proves:

- `74` unique, nonempty, relative FCF paths with no `..`;
- every record endpoint within the `941936`-byte raw frame;
- final cursor exactly `941936`, with zero trailing bytes;
- `44515` nonempty BPDQ records;
- every prefix valid, with maximum LCP `17`;
- the migrated literal member present.

Removing only those certified internal checks reduces the wrapper from `1885`
to `1381` bytes. The `269455`-byte source payload is unchanged, so package size
falls from `271340` to `270836` bytes, an exact `504`-byte saving.

A clean build used `337936` KiB peak RSS and reproduced the exact
`837176`-byte executable and `411996`-byte dictionary hashes. External corpus,
archive, subprocess, and output behavior remains checked. The successor has
zero score credit until its replacement native gate passes.
