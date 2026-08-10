# Versioned Releases

Mandate 2038 tracks two independently attributable artifacts:

1. **Executable game releases** preserve machine-readable rules, engine
   identity, replay contracts, and simulation inputs.
2. **Physical rules candidates** preserve the canonical player documents,
   their review protocol, and whether an executable version implements them.

`versions/current-release.json` is the mutable declaration for the next
release. Generate and verify the declared artifacts with:

```bash
npm run game:release
npm run game:release:verify
```

`versions/current.json` is the generated compatibility pointer consumed by
older runtime and physical-kit tooling. New release decisions belong in
`versions/current-release.json`; do not edit `current.json` by hand.

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
semantic version whenever its fingerprint changes. The release writer is
idempotent for byte-identical artifacts and fails closed if an existing
version path contains different bytes; only `versions/current.json` is updated
in place.
