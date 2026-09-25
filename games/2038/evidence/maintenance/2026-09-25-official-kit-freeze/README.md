# Official physical-kit freeze receipt

On 2026-09-25, `main` and `origin/main` both pointed to clean source
`a8169bc6b55738f4d14a375ac7943114e3b7ac06`. The latest Mandate-specific
source change remained `cd6eb434323a47dcb8f593e4025c6e40c37e405e`;
later repository commits did not revise Mandate content. `git push origin main`
reported everything up to date.

From `games/2038/`, `npm run game:release:verify` passed for executable
`0.21.2` and rules candidate `0.12.0-rc.8-test`, ruleset fingerprint
`sha256:cdfd3b6425101f38e73e15e4bd7ce40a98698c6e96f73206d90c4cccb67ec591`.
Then `npm run physical-kit:freeze` ran without `--local`, regenerated 28
content artifacts and the baseline gallery, and wrote
`dist/physical-kit/0.12.0-rc.8-test-a8169bc6/`.

The [retained kit manifest](kit-manifest.json), SHA-256
`9f1bdc6093cc97a13116b36adae7d28d82ce118a379c65e649f798d064ccfe46`,
records `sourcePublished: true`, 17 hashed kit files, and kit fingerprint
`sha256:47acf9c7db2ed0f3f7d5d48b9c12a51d0c651f4e7c8122c5fe9156667fbb55b4`.
The prior local-only `75e63240` receipt and published-source `cd6eb434`
kit were preserved. Generated `dist/` output was not hand-edited.

For a limited digital print inspection, Chrome printed the frozen component
masters to a 31-page letter PDF. The first project page was rasterized at
140 dpi as [project-print-proof.png](project-print-proof.png), SHA-256
`1827436658a98d5dda0460a07cd7022d1bc3a79e8641cb39fc6fdbdb0953a379`.
The visible Mega-Cluster and Fusion strips use the declared 150 × 85 mm fold
format, and their text appears within the borders in this rendering. This is
not an actual-size table handling test. It does not qualify crowded districts,
stacked attachments, Venture orientation, cube stability, or reading comfort.

No human session was conducted or recorded. The kit remains ready for a
four-player unfamiliar-player test using its `observer/` protocol. Questions,
missed effects, interventions, shuffled-Headline explanations, handling
problems, and understanding of the winner versus the World Ending still need
direct observation before any further layout or lore change is justified.

Component: Mandate 2038 physical-kit derivation and evidence. Intent:
preserved. Boundary effects: a published-source frozen kit and retained
identity receipt; no mechanic, lore, or component specification changed.
