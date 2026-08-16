# AGI Candidate greedy evolution v1

**Date:** 2026-08-15  
**Status:** rejected; optimizer clamp invalidated the training comparison  
**Game / rules:** `0.14.3` / `0.8.0-rc.4-test`  
**Source commit:** `41ac86c0`  
**Backend / players:** greedy / five

## Purpose

Train AGI Candidate against the exact backend and supported player count in
which Infrastructure Compounder produced credible head-to-head dominance.

## Invalid boundary

The canonical AGI Candidate assigns weight `60` to the Dossier Program. The
mutation helper applied a universal upper bound of `20`, so every non-baseline
candidate changed `agi_dossier: 60 → 20` before its seeded multiplicative
mutation could be compared. The first generation's apparent improvement from
`16.25%` to `24.58%` training win share is therefore confounded by an
unregistered forced normalization.

The final profile is not a valid candidate and must not enter a holdout or the
canonical browser strategy set.

## Correction

The mutation bound now preserves any authored starting weight above `20` as
that field's ceiling. The search may reduce the weight through its seeded
factor, but cannot silently replace it with `20`. A regression starts from a
weight of `60` and proves that one mutation remains above `20` and at or below
the authored ceiling.

## Artifact

- Seed: `mandate-2038-current-agi-greedy-evolution-v1`
- Raw report: `2026-08-15-current-agi-greedy-evolution-v1.raw.json`
- SHA-256:
  `67cb8345346d1ba9af0706721e2fd4826ad45e4815cc1bccd5febd4c705f7c59`

This is rejected training evidence, not a balance result.
