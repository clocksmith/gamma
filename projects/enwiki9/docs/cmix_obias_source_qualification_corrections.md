# cmix-obias Source Qualification Corrections

## Static failure diagnosis

`cmix_obias_source_1m_roundtrip_qm0_v1` exported the tracked Git tree, whose PGO
object was a Git-LFS pointer rather than the materialized profile. Its profile
hash check therefore failed before a valid archive comparison. q1 repaired the
LFS materialization, but the header/package command receipt lacked
`scratch_usage_before_cleanup`; q2 normalized that schema field. These are
infrastructure/receipt failures, not compression rejections.

## Arm B resource boundary

Arm B's active runner measures scratch only; it does not sample process-tree
RSS. The independent live receipt at
`operations/evidence/20260822T211458Z_cmix_obias_source_full1g_roundtrip_b_qm0_v1_live.json`
observed `VmRSS=10,231,140 KiB` and `VmHWM=10,360,428 KiB`, both above the frozen
9,765,625 KiB limit. Arm B must terminate unchanged, but it cannot pass the
strict resource gate on that evidence even if archive and inverse are exact.

## Evidence boundary

An exact Arm A/B archive match proves two-run determinism only for the bound
package and environment. It does not prove universal cross-CPU determinism.
The external candidate remains zero Gamma authorship and score credit. A
resource-qualified correction-only successor must preserve corpus, package,
parameters, source identity, and accounting boundary while adding process-tree
RSS sampling; it must not become a flag sweep.
