# Current Release Declaration

`current-release.json` declares the mutable current executable and physical
candidate identities. `npm run game:release` generates their immutable bundles
and the compatibility pointer `current.json` under `versions/`; never overwrite
an existing version directory.
