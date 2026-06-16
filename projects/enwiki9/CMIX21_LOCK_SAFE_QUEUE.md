# cmix21 Lock-Safe Queue

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
