# Migration Checklist

## Before Any Rename

- Confirm every active simulation, playtest, render, release, and local server
  process has exited or is intentionally stopped.
- Verify each active run has written its report, receipt, and source identity.
- Record the current commit plus every intentionally preserved dirty path. Do
  not combine unrelated worktree edits with the migration.
- Approve every proposed and unresolved entry in `path-map.json`.
- Replace every combined or prose intent with a one-source-to-one-destination
  entry, set `status` to `ready_to_apply`, and set `rules.applyAllowed` to true.
- Prepare the content compiler and graph source roots before moving any
  canonical content outside `content/`.
- Run `npm run migration:preflight -- --scope=all`; it must return success with
  an executable one-source-to-one-destination map.
- Run `npm run migration:audit -- --scope=all --include-archive
  --include-preserved-references` and preserve its output as the pre-migration
  reference inventory.
- Record generated-output policy: rebuild `data/` and build artifacts after the
  source move; do not hand-move them.

## Migration Sequence

1. Save the approved map, successful preflight, audit inventory, active-run
   attestation, and worktree record under `migration/receipts/<migration-id>/`.
2. Add destination-folder READMEs and a root repository map before moving code.
3. Update the content compiler and `content/graph.json` source-root policy,
   then move canonical source ownership and update graph paths.
4. Move implementation directories and update imports, package commands, and
   developer tasks.
5. Move evidence and build-output directories only after their producer and
   consumer paths are updated.
6. Leave `versions/` unchanged unless a separately approved archive migration
   creates a new release snapshot without rewriting historical bundles.
7. Regenerate projections and rendered outputs.

## Required Proof

- The default auditor reports zero live references to each approved old path.
  The archive-inclusive audit is an inventory only; immutable history is not
  rewritten merely to remove legacy path strings.
- Content build, validation, provenance lint, project check, and full tests pass.
- Browser routes load from the migrated local server.
- Markdown links and npm commands resolve.
- A new release snapshot verifies the migrated live tree.
- Independent reviews compare the migration manifest, changed paths, and
  auditor output for missing ownership or documentation changes.
