# CMIX-obias PPM0 Disk Joint q0 v3 Contract

## Purpose

This is a zero-credit infrastructure experiment. It tests whether forcing the
existing file-backed PPM mapping out of resident memory preserves the exact
arithmetic payload while using non-memory-backed scratch and satisfying the
resource, inverse, repeat, package, and cleanup boundaries on the opening
250,000-byte population.

It does not test a compression improvement and cannot earn objective savings.

## Frozen arms

- `P`: clean matched source build using the parent PPM residency policy.
- `N`: matched source build with `CMIX_PPMD_RSS_BUDGET_MB=0ULL`.

Both arms use the same source revision, corpus prefix, preprocessing,
probability model, arithmetic coder, package boundary, compiler family, and
disk-scratch helper. The only treatment difference is the compile-time PPM
residency budget.

## Frozen implementation identities

```text
clean runner SHA-256     26c5858bcd036b574618ddb367ed565b948045e2dd50652535695af00e723751
PPM0 runner SHA-256      1ca9f2d978b45a1ff30b638ffe3ddbb2fe9e68070f2b59de194048ebe4173c39
joint evaluator SHA-256  dbc171b46b55acd3514df925d8908c1922739ac1e699616db1ca28cd0248b8e1
disk helper SHA-256      4e29af0a4724a05bc8a1af467c428ed332c287445c991b21aa8bb39dbf829c08
```

The scratch root is supplied through `GAMMA_ENWIK9_DISK_SCRATCH` and must be
mounted on neither `tmpfs` nor `ramfs`. Each runner records the resolved mount,
source, filesystem type, options, and free bytes before execution.

## Required evidence

Each arm must produce a terminal receipt binding build definitions, executable
identity, input identity, encode and bare-decode return codes, durable payload
path, payload byte count, payload SHA-256, direct inverse identity, repeat
identity, process and process-tree resource maxima, scratch allocation before
cleanup, scratch allocation after cleanup, and package bytes.

The joint decision must require all of the following:

```text
P exact inverse
N exact inverse
P deterministic repeat
N deterministic repeat
P and N payload byte counts equal
P and N payload SHA-256 equal
P and N durable payload files directly byte-equal
N compile definition exactly CMIX_PPMD_RSS_BUDGET_MB=0ULL
all scratch mounts non-memory-backed
every process-tree RSS peak <= 9,765,625 KiB
every allocated scratch peak <= 100,000,000,000 bytes
all scratch removed after cleanup
incremental required package bytes <= 65,536
```

Equal payload size alone is insufficient. A missing durable payload, receipt,
hash, direct comparison, inverse, repeat, resource record, or cleanup record is
a failure, not an inferred pass.

## Decision boundary

A pass establishes only that PPM0 is a byte-preserving, disk-backed resource
correction on this frozen 250KB population. It authorizes subsequent candidates
to request the same correction under their own matched contracts. It does not
establish full-corpus memory compliance, archive savings, official eligibility,
or any Gamma compression credit.

A failure blocks use of PPM0 as qualified infrastructure. Any correction must
receive a new version and preserve this result unchanged.
