# DWNF-1: Deterministic Wrapper Normal Form

## Given

Let a wrapper be a finite deterministic orchestration system with these
observable operations:

```text
extract(A, R)
build(R, flags)
run(B, argv, environment, input_bytes)
read(output_path)
```

Here `A` is a finite source closure, `R` is a fresh private root, `B` is the
built executable, and every spawned process is deterministic. Paths below a
fresh root may differ between executions.

Two wrappers `W` and `W'` are supplied. They may differ in identifier names,
temporary-root names, source formatting, type annotations, comments, cache
syntax, and the placement of deterministic bookkeeping. Their externally
visible functions are

```text
compress : bytes -> bytes
decompress : bytes -> bytes.
```

## Questions

1. Define alpha-equivalence for private temporary roots and all descendant
   paths.
2. Give a labeled transition semantics for extraction, build caching,
   environment construction, process execution, and output reading.
3. Construct a bisimulation proving `W` and `W'` observationally equivalent
   when they:

   - extract identical ordered path-payload closures;
   - invoke the same build with the same effective flags;
   - produce identical executable and model hashes;
   - pass identical effective runtime argument vectors;
   - preserve the prior dynamic-library search path after the private root;
   - write identical input bytes and return identical output bytes.

4. Prove that shortening fresh path prefixes cannot change the observable
   result under path-alpha invariance.
5. Prove that removing comments, annotations, dead names, and redundant local
   variables preserves behavior when the transition labels are unchanged.
6. Give a finite certificate and verifier for a frozen pair of wrappers.
7. Derive the exact score transfer when the archive bytes agree and only the
   counted wrapper lengths differ.

## Frozen enwiki9 instance

`W` is the 2,294-byte normalized Compact5 wrapper and `W'` is its 1,099-byte
normal form. Both use the same 233,000-byte finite-family-minimum source
package, fixed `-T 4` runtime arguments, and fixed normalized build flags.

Native archive equality, roundtrip, determinism, runtime, and memory must still
be measured. The theorem alone receives zero Hutter score credit.
