# Versioned Releases

FRONTIER tracks two independently attributable artifacts:

1. **Executable game releases** preserve machine-readable rules, engine
   identity, replay contracts, and simulation inputs.
2. **Physical rules candidates** preserve the canonical rulebook, its review
   protocol, and whether an executable version implements it.

Generate and verify both from `data/game-version.json`:

```bash
npm run game:release
npm run game:release:verify
```

`versions/current.json` keeps the executable release in its backward-compatible
top-level fields and records the active physical candidate under
`rulesCandidate`.

An executable `manifest.json` contains ruleset, kit, engine, variant, and
contract fingerprints. It also fingerprints every canonical semantic-content
source. Its `game-bundle.json` preserves the exact content graph, JSON runtime
inputs, and generated playtest kit.

A physical-candidate `manifest.json` records `artifactKind:
physical-rules-candidate`, its document fingerprint, and an explicit
implementation status. Its `rules-candidate-bundle.json` preserves the actual
documents.

The two artifacts are not equivalent until the candidate manifest names a
non-null `implementedByGameVersion` and synchronized validation proves it.

Never overwrite a shared artifact with different contents. Assign a new
semantic version whenever its fingerprint changes.
