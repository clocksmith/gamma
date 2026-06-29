# cmix21 Lock-Safe Queue

## Current Fine-Valve Working Set

The active cmix21 search has moved from coarse memory divisors to fine PPMD
caps around the best observed archive/memory boundary. Treat this section as
the current strategy register; older observations below remain historical
audit context.

| candidate | role | known posture | next gate |
| --- | --- | --- | --- |
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Best nearby `10M` archive reference | Exact `10M` archive evidence exists at `1,638,083`, but the larger-scope RSS behavior made it unsuitable as the only live path. | Keep as archive-quality reference and memory-boundary control. |
| `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Active memory-margin candidate | Reported live posture: passed `1K`, `250K`, and `1M`; first `10M` archive pass reported `1,638,114`; determinism replay must finish before it counts as evidence. | If determinism and RSS pass, promote the same package to `100M` unchanged. |
| `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Deeper memory valve | Tracked as the lower-memory neighbor for cases where `ppmd22272k` still misses the RSS guard. | Run only if the higher-cap candidate fails the memory gate or needs a lower-RSS bracket. |
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

| surface | high-memory candidate | low-memory candidate | archive penalty | KiB saved | archive penalty per KiB saved | verdict |
|---|---|---|---:|---:|---:|---|
| PPMD cap | pending | pending | pending | pending | pending | pending |
| FXCM index map | pending | pending | pending | pending | pending | pending |
| FXCM RCM | pending | pending | pending | pending | pending | pending |
| PAQ RCM | pending | pending | pending | pending | pending | pending |
| rolling buffer | pending | pending | pending | pending | pending | pending |
| sparse maps | pending | pending | pending | pending | pending | pending |
| mmap allocator behavior | pending | pending | pending | pending | pending | pending |

Use:

```text
archive_penalty_per_kib_saved =
    (archive_bytes_lower_memory - archive_bytes_higher_memory)
  / (memory_kib_higher_memory - memory_kib_lower_memory)
```

The goal is not lowest memory. The goal is the least archive damage that creates
enough RSS margin for `100M`, then `1G`, while preserving deterministic replay.

## Active Constraint

At report start, the heavy lock was busy with:

```text
cmix21_text_mmap_paq5_ppmd50m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1
scope: 10000000
mode: --check-determinism
```

Later observation showed the visible lock holder had changed to:

```text
cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1
scope: 1024
mode: --check-determinism
```

The `ppmd50m_fxcmidx13div2` result directory currently shows 1K, 250K, and 1M
JSON evidence, but no recorded 10M JSON result in the checked snapshot.

No additional cmix21 gate was launched for this queue report.

## Live Audit Summary

Read-only `candidate_audit.py --json` reports:

```text
program directories: 473
registered programs: 223
track_source_before_evolution: 23
untracked nonignored entries: 93
modified tracked entries: 7
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
4. For the active 10M candidate, record the result before changing ledgers.
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
  the active 10M run has been recorded.
- Keep the public `fx2-cmix` reproduction lane separate from the cmix21 queue.
  It anchors official accounting; it is not a replacement for the active
  memory-shaped candidate promotion path.
