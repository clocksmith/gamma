# Solution: Dependency-Closure Package

Let `C` be the set of vertices reachable from `R`.

Every root reaches itself by a path of length zero, so `R` is contained in
`C`. If `u` is in `C` and `(u,v)` is an edge, append that edge to a path from
`R` to `u`; this gives a path from `R` to `v`. Hence `v` is in `C`, proving
that `C` is dependency-closed.

Now let `S` be any dependency-closed package containing `R`. Induct on path
length. Every length-zero reachable vertex is a root and lies in `S`. If a
reachable vertex `v` has a path ending in `(u,v)`, the induction hypothesis
places `u` in `S`, and closure places `v` in `S`. Therefore `C` is a subset of
every valid `S`.

Thus `C` is valid and contained in every valid package. It is the unique
inclusion-minimal package. If all vertex costs are strictly positive, every
proper superset has strictly larger cost, so `C` is also the unique
minimum-cost package.

A canonical construction performs breadth-first search from roots in their
supplied order, visiting outgoing neighbors in identifier order. The emitted
package list is sorted by identifier. A verifier recomputes reachability,
checks equality with the submitted list, and then checks the canonical
serialization.

## Frozen NC5 result

The stated CPU closure was serialized from the SHA-256-pinned official source
using:

```text
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner
```

followed by gzip. The result is:

```text
311,289 bytes
SHA-256 79e5e7152ef2b419528157ae86e14570b0a87a4cb12765628963d415522f0102
```

Extracting this package and running its Makefile produced a 468,184-byte CPU
binary successfully. The 311,289-byte package leaves 388,711 bytes under
NC5's provisional 700,000-byte package cap for launch wrappers and any
submission framing. It receives zero score credit before the complete
candidate is frozen and measured.
