# Gammatron #88: both matchers on both frozen suites

Merged source `a6a9a6bfe` (contains reconcile `fb7488a64` and the write-boundary
prerequisite guard). Candidate: `SuffixIndex` (`suffix-index-v1`, run.js `--matcher index`).
Ablation: the older profile matcher (`suffix-eligibility-v4`, run.js `--matcher profile`).
Baseline: exact state-hash matching. No model calls, no tenant, no spend.

## Result, 2026-11-21

| Suite | Exact hash | Profile matcher | SuffixIndex |
| --- | ---: | ---: | ---: |
| Sandbox families, 32 held-out variants: planner calls | 124 | **20** | 124 |
| Sandbox families: reused steps | 16 | 120 | 16 |
| Sandbox families: certified rejoin rate, k ≤ 2 | 0.125 | 0.875 | 0.125 |
| Sandbox families, 24 adversarial near-misses: unsafe certifications | 0 | 0 | 0 |
| Workflow generalization, 26 runs: decisions without resume | 93 | 93 | **64** |
| Workflow generalization: decisions with resume | 59 | 59 | **29** |
| Workflow generalization: certified rejoins (no resume / resume) | 0 / 0 | 0 / 0 | 23 / 30 |
| Workflow generalization: wrong-context writes, submissions | 0, 0 | 0, 0 | 0, 0 |

- Each matcher gains only on the suite built alongside it, and neither gains at all on
  the other's. The merged revision reproduces both earlier results exactly (Stage 1:
  124 to 20; generalization: 93 to 64 and 59 to 29).
- SuffixIndex is safe on all 24 near-misses, but vacuously: it certified nothing on any
  sandbox case. Its refusals there were `prefix-unaccounted` (1,008) and
  `page-mismatch` (168). The taught index was populated (7 nodes per family). So the
  near-miss suite does not yet test SuffixIndex's certification path.
- The profile matcher certified on 8 near-miss runs, none unsafe: NM5 (4) rejoins
  legitimately and still clicks the required approval; NM4 (4) is caught at the review
  boundary and the node is demoted to exact-prefix, as designed.
- Every run met its expected behaviour in all arms; graphs and indexes unchanged.

## Files

- `stage1-three-arm.json`: full Stage 1 receipt with per-case rows, including
  SuffixIndex refusal counts. Produced in a clean worktree at `a6a9a6bfe` plus the
  harness change committed with this file.
- `workflow-generalization-both-matchers.json`: per-arm totals and report digests for
  both run.js runs (headless Chrome 158.0.8127.36). `sourceDirty` is true only because of
  an untracked `node_modules` symlink.

## Reproduce

```sh
node projects/workspace/qualification/stage1-suffix-ablation.js OUT.json \
  --arms exact-hash-v3,suffix-eligibility-v4,suffix-index-v1   # exits 1: index gates fail
for m in index profile; do
  node projects/workspace/qualification/workflow-generalization/run.js --controlled \
    --matcher $m --arms whole,suffix,whole-rc,suffix-rc --out NEW_DIR_$m
done
```

## What this means for #88

Neither matcher is a general improvement yet; the frozen suites disagree completely.
The 21-pair independent holdout (`../independent-holdout/`) is separate evidence: it ran
at `5b79bcecc`, before SuffixIndex reached main, so it tested only the profile matcher. Before choosing SuffixIndex as the shipped matcher, either add
sandbox cases whose prefix is accounted so its certification path faces the
near-misses, or explain why the sandbox prefixes should be refused.
