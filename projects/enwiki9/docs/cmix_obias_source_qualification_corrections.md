# cmix-obias Source Qualification Corrections

## Static failure diagnosis

`cmix_obias_source_1m_roundtrip_qm0_v1` exported the tracked Git tree, whose PGO
object was a Git-LFS pointer rather than the materialized profile. Its profile
hash check therefore failed before a valid archive comparison. q1 repaired the
LFS materialization, but the header/package command receipt lacked
`scratch_usage_before_cleanup`; q2 normalized that schema field. These are
infrastructure/receipt failures, not compression rejections.

## Arm B resource boundary

Arm B's runner measured scratch only; it did not sample process-tree RSS. The
independent live receipt at
`operations/evidence/20260822T211458Z_cmix_obias_source_full1g_roundtrip_b_qm0_v1_live.json`
observed `VmRSS=10,231,140 KiB` and `VmHWM=10,360,428 KiB`, both above the frozen
9,765,625 KiB limit. The terminal memory observation later preserved
`VmHWM=10,425,744 KiB`. Arm B's encode reproduced Arm A byte-for-byte, but its
decode stopped at `39.07%` when the enclosing scope failed with `oom-kill`.
Arm B is now terminal, cannot pass the strict resource or exact-inverse gate,
and must remain unchanged. Its stale live sidecars were archived into the
result before removal; its incomplete `/dev/shm` scratch remains retained.

## Evidence boundary

An exact Arm A/B archive match proves two-run determinism only for the bound
package and environment. It does not prove universal cross-CPU determinism.
The external candidate remains zero Gamma authorship and score credit. A
resource-qualified correction-only successor must preserve corpus, package,
parameters, source identity, and accounting boundary while adding process-tree
RSS sampling; it must not become a flag sweep.

Terminal evidence is bound by
`results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-receipt.json`
and its independent `oom-terminal-verification.json`. The terminal A/B audit
is `results/cmix_obias_source_full1g_ab_terminal_audit_v2/decision.json` and
correctly fails both its joint correctness and strict-resource verdicts.

## q1 correction chain

The file-backed q1 implementation is frozen under its 30-file program lock.
Its correction chain preserves infrastructure failures instead of rewriting
them:

- qm5 completed source closure, independent builds, and controls. Its guarded
  traced-package build failed before scientific work because the guard sampled
  the outer process while it still had 32 allowed CPUs; `taskset` was inside
  the guarded command. The immutable guard reports
  `logical_cpu_guard_exceeded` and return code `-15`.
- qm6 moved CPU affinity outside the guard. Its traced build passed and its
  opening 250KB parent/q1 scope was exact. The v1 runner then rejected the
  middle parent because it restored 249,871 bytes, not the raw 250,000-byte
  fragment. This exposed a contract error: the Wikipedia preprocessor is not
  independently raw-invertible when reset on an arbitrary interior slice.
- qm7 uses the v2 contract. Raw inverse is mandatory at offset zero; middle
  and tail require exact parent/q1 restored-stream identity. All three scopes
  pass exact probability, full trace, payload, decoded identity, resource, and
  cleanup checks. The opening cumulative 1M successor passes the same checks
  and exact raw inversion.

The package-level allocator event stream is not treated as one lifecycle.
The main package process and two helper CMIX processes inherit the same event
descriptor, producing three concatenated 79-event namespaces. Allocator
lifecycle authority instead binds the isolated positive fixture and all 15
negative controls. Codec executions independently require that q1's backing
directories are empty after encode and decode.

The qm7 evidence grants no full-stream identity or Hutter score credit. It
authorizes only the bounded opening/distant 10M identity phase. The distant
trajectory begins from cold reset at corpus offset 500,000,000 and is a
transfer diagnostic, not evidence for the byte-zero persistent state at that
offset.
