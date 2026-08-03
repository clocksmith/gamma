# Current Release Declaration

`game-version.json` declares the mutable current executable and physical
candidate identities. `npm run game:release` generates their immutable bundles
under `versions/`; never overwrite an existing version directory.
