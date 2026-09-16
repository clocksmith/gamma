# Trimmed FX2: restricted load-time dependency evidence

The frozen trimmed executable loads with exactly four shared libraries and the
ELF loader in an otherwise empty filesystem. This resolves the transitive
**ELF load-time inventory on this host**. It does not establish the files needed
by an actual compression or decompression, licensing closure, target-machine
compatibility, or a complete submission package.

The executable is the measured trimmed parent, 438,792 bytes, SHA-256
`1bbae21a0a5a8e50669bce1e68f565296155af4b7610c2a7ac079b8d8f4aa890`.
Neither it nor the source packages of the active 10MB or held feedback gate
were changed.

## What was executed

[The bounded audit](../tools/fx2_trim_load_closure_v1.py) identifies the actual
host providers, records their bytes and hashes, follows every `DT_NEEDED` edge,
and verifies each provider's `SONAME`. It then invokes the loader with `--list`
inside an empty Bubblewrap filesystem. Only the binary and the five identified
runtime files are mounted. The library cache is disabled, the environment is
cleared, the library search path is explicit, and networking is isolated.
There is no whole-`/usr` mount. The loader does not enter codec main.

| Object | Required providers |
| --- | --- |
| `cmix` | `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6` |
| `libstdc++.so.6` | `libm.so.6`, `libc.so.6`, loader, `libgcc_s.so.1` |
| `libm.so.6` | `libc.so.6`, loader |
| `libgcc_s.so.1` | `libc.so.6`, loader |
| `libc.so.6` | loader |
| loader | none |

The positive listing succeeds. Four controls each omit one required shared
library; every control exits 127 and names that missing library. All supplied
files retain their original hashes. Local package ownership is also recorded;
it is provenance, not a license determination.

The five runtime files occupy **6,566,680 bytes** in their current host forms.
This is a file inventory, not an extra score charge or a claim of exemption.
The final packaging arrangement and permitted target-platform facilities must
determine their treatment. The prior static audit's GLIBC 2.38 and GLIBCXX
3.4.29 requirements remain unchanged.

## Preserved implementation failure

The first audit's restricted loader listing succeeded, but the parser rejected
the explicit mapping of `/lib64/ld-linux-x86-64.so.2` into `/runtime/lib`.
[Its source and outputs](../operations/provenance/fx2_trim_load_closure_20260916/failure.json)
are retained. The correction requires that exact mapping separately, while
still requiring the four expected shared libraries. The successful successor
uses a new output directory. No codec or scientific parameter changed.

## Remaining boundary

Actual encode/decode can open assets, create scratch, or dynamically load code
that a loader listing does not exercise. A separately admitted restricted
filesystem replay must therefore include the exact model, dictionary, commands,
input/output paths, and scratch behavior. Build tools are a separate closure.
Copied-header lineage, model-specific permission, and the declared libdevice
transcription remain unresolved; this audit makes no legal conclusion.

There is zero compression credit and no full-corpus score. The active 10MB
trim comparison proceeds unchanged. The frozen value-feedback gate remains
held until its resource admission is possible.

Evidence: [successful receipt](../operations/provenance/fx2_trim_load_closure_20260916_v2/receipt.json),
[restricted listing](../operations/provenance/fx2_trim_load_closure_20260916_v2/restricted-loader-list.json),
[prior static ELF audit](../operations/provenance/fx2_trim_runtime_static_audit_20260915.json).
