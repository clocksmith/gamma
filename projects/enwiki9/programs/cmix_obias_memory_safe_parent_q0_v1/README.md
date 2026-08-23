# cmix-obias memory-safe parent q0 v1

This is a dormant, correction-only implementation successor for the external
`cmix-obias` parent. It does not change model capacity, prediction logic,
arithmetic coding, preprocessing bytes, or package accounting.

## Why this successor exists

Read-only Arm B evidence at 77.62 percent showed:

```text
VmHWM                         10,435,724 KiB
strict decimal ceiling        9,765,625 KiB
excess                          670,099 KiB
concurrent VmRSS              8,508,652 KiB
```

The live process was single-threaded and predominantly anonymous. Four fully
resident 512 MiB mappings correspond exactly to `ContextMap3` tables whose
256 MiB source parameters are doubled internally. Those tables are live model
state and are deliberately unchanged.

The same process carried a sparse 14,000 MiB `ppm.temp` mapping whose residency
is already controlled by output-neutral `MADV_DONTNEED`. The source default
waits until total RSS reaches 9,216 MiB before purging. This successor lowers
that trigger to 8,192 MiB and returns freed preprocessing allocator pages
immediately before constructing `Predictor`.

## Scientific boundary

The output-neutral claim is a hypothesis until actual evidence proves:

```text
integer probability identity
parent/child out.cmix payload byte identity
exact canonical inverse
child A/B out.cmix payload identity
child A/B archive identity
strict resource compliance
```

The parent and child executables are intentionally different, so their
self-extracting archives are not expected to match. Any parent/child
probability or payload mismatch creates a new compression candidate. Any child
A/B archive mismatch fails repeat determinism. A memory pass earns no
compression savings; it only establishes an eligible exact parent for the CMIX
full-midpoint oracle and later Gamma-authored adaptation.

No command in this directory launches an experiment. Apply the patch only to
the exact source hashes in `manifest.json`, after Arm B terminalizes or on a
separately isolated host, and bind the run to resource-guard receipt v3.

From this directory, the fail-closed application command is:

```text
sh ./apply_memory_safe_parent.sh /path/to/bound/source/root
```

## Full-corpus qualification

The dormant runners are:

```text
projects/enwiki9/tools/cmix_obias_memory_safe_parent_full1g_roundtrip_a_q0_v1.py
projects/enwiki9/tools/cmix_obias_memory_safe_parent_full1g_roundtrip_b_q0_v1.py
```

They fail closed unless `program-lock.json` exists beside this README and
binds an independently built compressor, neural head, source inputs, patch,
and build receipt. The lock contract is `program-lock.schema.json`.

Resource qualification is external and must come from a v3 guard receipt;
neither runner grants promotion authority by itself.

## Independent-build authority

Each clean cache-disabled build must emit a receipt conforming to
`build-receipt.schema.json`. Build A and build B must use distinct build roots
while binding identical source, patch, compiler, linker, flags, environment,
and command contracts.

After both builds terminate, materialize the comparison receipt and activation
lock with:

```text
python3 projects/enwiki9/tools/materialize_cmix_obias_memory_safe_program_lock.py \
  --receipt-a PROJECT_RELATIVE_BUILD_A_RECEIPT \
  --receipt-b PROJECT_RELATIVE_BUILD_B_RECEIPT \
  --comparison-receipt PROJECT_RELATIVE_COMPARISON_RECEIPT
```

The command fails closed on any provenance or output mismatch and refuses to
replace either an existing comparison receipt or `program-lock.json`. The
comparison receipt grants build-identity authority only. It does not authorize
compression execution or promotion.

Produce the two receipts sequentially after the exclusive full-1G lease is
released:

```text
python3 projects/enwiki9/tools/build_cmix_obias_memory_safe_parent_q0_v1.py --arm a
python3 projects/enwiki9/tools/build_cmix_obias_memory_safe_parent_q0_v1.py --arm b
```

The builder refuses to run while the imported Arm B lease is live. It
materializes the exact shipped Git-LFS PGO profile and keeps the original
PGO/LTO, floating-point, native-architecture, strip, section-removal, UPX, and
asset-packaging contracts. A true PGO incompatibility is terminal evidence;
the builder does not suppress it or silently substitute a profile.
