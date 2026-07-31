# Layout Migration Planning

This directory prepares a future repository-layout migration while a live
simulation may still be reading the current tree. Nothing here moves or edits
live game files.

## Status

Planning only. The tools here never move or edit live game files.

- `audit.mjs` reads text files and reports literal old-path references.
- `preflight.mjs` checks whether a selected scope has an executable mapping,
  whether its source and destination states are safe, whether the content graph
  can accept the planned source roots, and lists blockers.
- `target-layout.md` records the decisions still required before a one-sweep
  migration can be authorized.

## Inputs

- `path-map.json` distinguishes confirmed moves from proposals that still need
  a product decision.
- `checklist.md` defines the stop conditions, migration sequence, and required
  evidence before any filesystem rename.

## Use

```bash
npm run migration:audit -- --scope=confirmed
npm run migration:audit -- --scope=proposed
npm run migration:audit -- --scope=all --include-archive --include-preserved-references
npm run migration:preflight -- --scope=confirmed
npm run migration:preflight -- --scope=all
```

The tools also accept `--scope all`, but the `--scope=value` form is the
documented form and avoids ambiguity in copied commands.

The default scan excludes immutable `versions/` artifacts. Use
`--include-archive` only to measure historical references; archive paths are
not migration targets. The normal report lists only live references. It counts
generated `dist/` references and preserved study/playtest evidence separately;
add `--include-preserved-references` when saving the full pre-migration
inventory.

`preflight.mjs` is intentionally non-zero while any mapping is proposed,
unresolved, non-literal, or the repository is marked planning-only. A passing
preflight is necessary, not sufficient: the active-run gate and full
post-migration verification in `checklist.md` still apply.

## Known preparation requirements

- `content/physical/ → physical/` cannot be moved until the content compiler
  and `content/graph.json` explicitly allow `physical/` as a canonical source
  root. The preflight reports every affected graph source until that preparatory
  change exists.
- Every entry in `path-map.json` must be one literal source directory and one
  literal destination directory. Combined intents such as “tools and scripts”
  belong in the unresolved decision list until they are split.
- `versions/` remains immutable historical evidence. It is not part of this
  migration without a separately approved archive policy and a fresh verified
  release snapshot.
