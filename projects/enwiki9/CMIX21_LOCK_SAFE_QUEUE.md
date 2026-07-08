# cmix21 Lock-Safe Queue

## Current Fine-Valve Working Set

The active cmix21 search has moved from coarse memory divisors to fine PPMD
caps around the best observed archive/memory boundary. Treat this section as
the current strategy register; older observations below remain historical
audit context.

| candidate | role | known posture | current or next action |
| --- | --- | --- | --- |
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Best nearby `10M` archive reference | Exact `10M` archive evidence exists at `1,638,083`, but the larger-scope RSS behavior made it unsuitable as the only live path. | Keep as archive-quality reference and memory-boundary control. |
| `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Narrow memory-margin candidate | Exact `10M` replay passed at archive `1,638,114`, local score `2,202,389`, roundtrip true, determinism true, and max sampled single RSS `10,482,852` KiB under the `10,485,760` KiB guard. Unchanged `100M` promotion crossed the same guard by `36` KiB before producing a scored archive or roundtrip. | Keep as the upper bracket for the current PPMD memory valve. Do not retune it unless bracketing data says this surface is still cheapest. |
| `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Deeper memory valve, now bracketed | Exact no-ceiling `10M` replay passed at archive `1,638,182`, local score `2,202,456`, program size `564,274`, roundtrip true, determinism true, and max sampled single RSS `10,482,468` KiB. The unchanged `100M` promotion failed the local RSS guard at `10,485,796` KiB, `36` KiB over the `10,485,760` KiB guard, before producing a scored archive or roundtrip. | Keep as the upper bracket for the next PPMD-only cut. Do not rerun unchanged at `100M` unless the guard policy changes. |
| `cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Deeper memory valve, now bracketed | Packaged from `ppmd21888k` with `-DCMIX_PPMD_MEMORY_KB=21760`; program size `564,273`. Exact `1K`, `250K`, `1M`, and `10M` replays passed. The exact `10M` replay produced archive `1,638,204`, local score `2,202,477`, roundtrip true, determinism true, and max sampled single RSS `10,482,248` KiB. The unchanged `100M` promotion failed the local RSS guard by `72` KiB before producing a scored archive or roundtrip. | Keep as the upper bracket for the active PPMD-only cut. Do not rerun unchanged at `100M` unless the guard policy changes. |
| `cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Deeper memory valve, now bracketed | Packaged from `ppmd21760k` with `-DCMIX_PPMD_MEMORY_KB=21632`; program size `564,274`. Exact `1K`, `250K`, `1M`, and `10M` replays passed. The exact `10M` replay produced archive `1,638,229`, local score `2,202,503`, roundtrip true, determinism true, and max sampled single RSS `10,482,244` KiB. The unchanged `100M` promotion failed the local RSS guard by `68` KiB before producing a scored archive or roundtrip. | Keep as the upper bracket for the active PPMD-only cut. Do not rerun unchanged at `100M` unless the guard policy changes. |
| `cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Deeper memory valve, now bracketed | Packaged from `ppmd21632k` with `-DCMIX_PPMD_MEMORY_KB=21504`; program size `564,273`. Exact `10M` replay passed at archive `1,638,165`, local score `2,202,438`, roundtrip true, determinism true, and max sampled single RSS `10,482,116` KiB, `3,644` KiB under the local binary guard. The unchanged `100M` promotion failed the local RSS guard by `72` KiB before producing a scored archive or roundtrip. | Keep as the upper bracket for the active PPMD-only cut. Do not rerun unchanged at `100M` unless the guard policy changes. |
| `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Deeper memory valve, now bracketed | Packaged from `ppmd21504k` with `-DCMIX_PPMD_MEMORY_KB=21376`; program size `564,274`. Exact `1K`, `250K`, `1M`, and `10M` replays passed. The unchanged `100M` promotion failed the local RSS guard by `116` KiB before producing a scored archive or roundtrip. | Keep as the upper bracket for the active PPMD-only cut. Do not rerun unchanged at `100M` unless the guard policy changes. |
| `cmix21_text_mmap_paq5_ppmd21248k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Bracketed upper candidate | Packaged from `ppmd21376k` with `-DCMIX_PPMD_MEMORY_KB=21248`; program size `564,274`. Exact `1K`, `250K`, `1M`, and `10M` replays passed. The unchanged `100M` promotion failed the local RSS guard by `64` KiB before producing a scored archive or roundtrip. | Keep as the upper bracket for the active PPMD-only cut. |
| `cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Active prefix-ladder candidate | Packaged from `ppmd21248k` with `-DCMIX_PPMD_MEMORY_KB=21120`; program size `564,274`. Exact `1K` replay passed at archive `247`, roundtrip true, determinism true, and max sampled single RSS `8,624,384` KiB. | Run the unchanged `250K` replay next. If it passes, record it and promote unchanged to `1M`; if it fails by RSS, record the bracket and inspect non-PPMD memory surfaces. |
| `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Historical high-quality boundary | Best nearby archive family, but memory-fragile at larger scope. | Keep as baseline for bytes lost per KiB saved. |
| `cmix21_text_mmap_paq5_ppmd21m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Coarse lower-memory bracket | Bought memory margin but cost archive bytes versus the `22m` family. | Use only as a lower-bound control for the PPMD memory derivative. |

Promotion rule:

```text
Do not retune between gates unless the current candidate fails.
The same package must pass compression, decode, determinism replay, and RSS
before moving from 10M to 100M, then from 100M to 1G.
```

Evidence rule:

```text
First-pass archive bytes are not a result row until replay/determinism and
roundtrip status are recorded in a result artifact or a structured report.
```

## Official Accounting And Memory Unit Risk

The cmix21 queue uses local proxy packages to screen candidates, but a final
Hutter-facing result must be audited as:

```text
submission score = comp9/source-package bytes + archive9 bytes
```

Count every required artifact: wrapper code, build or source package, compressed
binary payload, dictionaries, static tables, command-line options, and any
configuration needed to reproduce `enwik9`. Prefix gates remain search evidence
until the full corpus is replayed and this accounting is complete.

Current RSS guards use the binary limit:

```text
10GiB = 10,485,760 KiB
```

A stricter decimal reading is:

```text
10GB = 9,765,625 KiB
```

Therefore a candidate that passes the local guard with a narrow margin should be
called locally admissible, not submission-grade. Promotion notes must include
the guard used, peak sampled single-process RSS, and whether the candidate has
meaningful margin for the next scope.

## Memory-Value Table Contract

For every fine-valve candidate, add a row to a memory-value table once exact
same-scope evidence exists:

The generated view is `docs/cmix21_memory_valves.md`, produced by:

```bash
python3 projects/enwiki9/tools/cmix21_memory_valve_report.py
```

| surface | high-memory candidate | low-memory candidate | archive penalty | KiB saved | archive penalty per KiB saved | verdict |
|---|---|---|---:|---:|---:|---|
| PPMD cap | `ppmd22400k` | `ppmd22272k` | `31` bytes at `10M` | `128` KiB cap cut | `0.2421875` bytes/KiB | `ppmd22272k` passed exact `10M` but failed `100M` RSS by `36` KiB; keep as upper bracket. |
| PPMD cap | `ppmd22272k` | `ppmd21888k` | `68` bytes at exact deterministic `10M` | `384` KiB cap cut | `0.1770833` bytes/KiB | Lower-memory replay passed with roundtrip/determinism and `3,292` KiB local RSS margin, but unchanged `100M` failed RSS by `36` KiB. |
| PPMD cap | `ppmd22400k` | `ppmd21888k` | `99` bytes at exact deterministic `10M` | `512` KiB cap cut | `0.1933594` bytes/KiB | Coarse bracket: `ppmd21888k` preserved archive slope but still did not clear the unchanged `100M` RSS guard. |
| PPMD cap | `ppmd21888k` | `ppmd21760k` | `22` bytes at exact deterministic `10M` | `128` KiB cap cut | `0.171875` bytes/KiB | `ppmd21760k` passed exact `10M` but failed unchanged `100M` RSS by `72` KiB; keep as upper bracket. |
| PPMD cap | `ppmd21760k` | `ppmd21632k` | `25` bytes at exact deterministic `10M` | `128` KiB cap cut | `0.1953125` bytes/KiB | `ppmd21632k` passed exact `10M` but failed unchanged `100M` RSS by `68` KiB; keep as upper bracket. |
| PPMD cap | `ppmd21632k` | `ppmd21504k` | `-64` bytes at exact deterministic `10M` | `128` KiB cap cut | `-0.5` bytes/KiB | `ppmd21504k` improved the exact `10M` archive while cutting memory, but unchanged `100M` failed RSS by `72` KiB; keep as an upper bracket. |
| PPMD cap | `ppmd21504k` | `ppmd21376k` | measured after exact gate replay | `128` KiB cap cut | see generated valve report | `ppmd21376k` preserved prefix determinism but failed unchanged `100M` RSS by `116` KiB. |
| PPMD cap | `ppmd21376k` | `ppmd21248k` | measured after exact gate replay | `128` KiB cap cut | see generated valve report | `ppmd21248k` preserved prefix determinism but failed unchanged `100M` RSS by `64` KiB. |
| PPMD cap | `ppmd21248k` | `ppmd21120k` | restart gate ladder in progress | `128` KiB cap cut | pending exact paired rows | `ppmd21120k` passed exact `1K`; active `250K` gate is launchable. |
| FXCM index map | unmeasured | unmeasured | no paired same-scope row | no measured KiB delta | not computed | Do not cut this surface until PPMD bracketing fails or exact ablation receipts identify a cheaper KiB source. |
| FXCM RCM | unmeasured | unmeasured | no paired same-scope row | no measured KiB delta | not computed | Earlier FXCM RCM divisor changes can break decode; require prefix gates from `1K` before any promotion. |
| PAQ RCM | unmeasured | unmeasured | no paired same-scope row | no measured KiB delta | not computed | Keep primary PAQ history continuity protected unless an exact memory-value pair beats the PPMD valve. |
| rolling buffer | unmeasured | unmeasured | no paired same-scope row | no measured KiB delta | not computed | Treat as a fallback only after map/cap surfaces fail; buffer cuts can damage match locality. |
| sparse maps | unmeasured | unmeasured | no paired same-scope row | no measured KiB delta | not computed | Measure only one sparse-map family at a time so archive penalties can be attributed. |
| mmap allocator behavior | unmeasured | unmeasured | no paired same-scope row | no measured KiB delta | not computed | Use only for allocator overhead or fragmentation evidence; do not count allocator changes as model regularization without proof. |

Use:

```text
archive_penalty_per_kib_saved =
    (archive_bytes_lower_memory - archive_bytes_higher_memory)
  / (memory_kib_higher_memory - memory_kib_lower_memory)
```

The goal is not lowest memory. The goal is the least archive damage that creates
enough RSS margin for `100M`, then `1G`, while preserving deterministic replay.

## Active Constraint

The active heavy-lock candidate is the next PPMD-only cut:

```text
cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1
scope: 250000
mode: --check-determinism
guard receipt: ppmd21120k_250000_determinism_rss_guard.json
```

This candidate exists because `ppmd21248k` passed exact prefix replays but
failed the unchanged `100M` promotion by RSS guard before a scored archive was
produced. The exact `1K` replay passed; the active gate is the unchanged
`250K` determinism replay. The active gate remains incomplete until both the
driver result JSON and RSS guard JSON are terminal. No secondary heavy gate,
package build, or result-corpus CPU sweep should be launched while a gate owns
the lock.

If this gate passes:

```text
record exact result -> regenerate receipts -> promote the same package unchanged
```

If this gate fails by RSS:

```text
record RSS failure -> package the next lower PPMD-only cut -> restart prefix gates from 1K
```

## Parallel Work Policy

The host may have enough total RAM and CPU threads for multiple processes, but
the proof lane is serialized for attribution and resource-boundary hygiene. A
full compression gate owns `/tmp/enwiki9-heavy.lock` because its temp files,
native allocator behavior, and peak RSS decide whether the package is admissible.
Running a second full scorer at the same time would make memory and I/O effects
harder to attribute to a single candidate.

Safe parallel work while the heavy lock is held:

```text
refresh status and certificate receipts
audit existing result JSONs
edit documentation and accounting ledgers
run cached-log or shadow-coder probes with bounded RSS and reduced priority
inspect source and package metadata without mutating the active candidate
```

Unsafe parallel work while the heavy lock is held:

```text
launch another compression/decompression gate
package a fallback candidate
run result-corpus forecast sweeps
change active candidate source or registry metadata
```

This is why SRSTC shadow scoring can run beside the cmix21 gate when it is
explicitly reduced-priority and low-RSS, while another `100M` or `1G` compressor
gate must wait for a terminal receipt.

## Live Audit Summary

Read-only `candidate_audit.py --json` reports:

```text
program directories: 515
registered programs: 223
active: 24
candidate: 67
measured_negative: 77
blocked_dependency: 12
retired: 334
untracked nonignored entries: 28
modified tracked entries: 20
```

The generated inventory's source-tracking subset currently contains 16 entries;
all 16 import cleanly and expose `compress`/`decompress`. The generated
inventory's full `candidate` subset contains 63 entries; all 63 also import
cleanly. The live audit sees 23 source-tracking entries, so
`candidate_inventory.json` is stale relative to the filesystem.

The blockers are source registration, payload tracking, and evidence state, not
Python contract shape.

## Highest-Value Source-Tracking Rows

These have useful local evidence but are still blocked by source/registry state.

| candidate | registered | blockers | best known evidence |
| --- | --- | --- | --- |
| `cmix21_text_mmap_paq5_ppmd50m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | no | `not_in_index_json`, `has_untracked_source_files` | 1M archive `174415`, score `734342` |
| `cmix21_text_mmap_paq5_ppmd60m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | no | `not_in_index_json`, `has_untracked_source_files` | 1M archive `174415`, score `734342` |
| `cmix21_text_mmap_paq5_ppmd74m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | no | `not_in_index_json`, `has_untracked_source_files` | 1M archive `174415`, score `734340` |
| `cmix21_text_mmap_paq5_ppmd70m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | no | `not_in_index_json`, `has_untracked_source_files` | 1M archive `174415`, score `735689` |
| `cmix21_text_mmap_paq5_ppmd75m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1` | no | `not_in_index_json`, `has_untracked_source_files` | 1M archive `174415`, score `735694` |
| `cmix21_text_mmap_paq5_ppmd75m_fxcmrcm24_rcm32_bufthirtysecond_minmaps_v1` | yes | `has_untracked_source_files` | 250K archive `45184`, score `606401` |
| `cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1` | yes | `has_untracked_source_files` | 250K archive `45182`, score `606464` |

## Cleanup Decision Rules

1. For variants with the same archive and different counted score, keep only the
   smallest counted package unless a memory or determinism result distinguishes
   them.
2. For variants not in `index.json`, either register them intentionally or mark
   them retired. Leaving them as unregistered candidate folders keeps the audit
   queue noisy.
3. For registered variants with `has_untracked_source_files`, serialize the
   package source state before promotion. Do not evolve those folders further
   until the source boundary is reproducible.
4. For the active heavy-lock candidate, record the gate result before changing
   ledgers or retuning memory surfaces.
5. For fine PPMD valves, compute the local derivative explicitly:

   ```text
   archive_penalty_per_kib_saved =
       (archive_bytes_lower_memory - archive_bytes_higher_memory)
     / (ppmd_kib_higher_memory - ppmd_kib_lower_memory)
   ```

   Prefer the smallest memory reduction that creates enough RSS margin.

## Immediate Non-Scoring Work

- Decide whether the `ppmd50m`, `ppmd60m`, and `ppmd74m` `fxcmidx13div2`
  variants are distinct enough to keep. Their 1M archive is identical in the
  current audit snapshot.
- Register the one chosen `fxcmidx13div2` row or explicitly retire the
  duplicates.
- Preserve the source payload for the registered `fxcmrcm24` and `fxcmrcm28safe`
  rows before running more gates.
- Refresh `candidate_inventory.json` and `CANDIDATE_INVENTORY.md` only after
  the active heavy-lock gate has been recorded or failed with a guard receipt.
- Keep the public `fx2-cmix` reproduction lane separate from the cmix21 queue.
  It anchors official accounting; it is not a replacement for the active
  memory-shaped candidate promotion path.
