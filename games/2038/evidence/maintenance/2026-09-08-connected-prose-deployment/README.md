# Connected-prose deployment: September 8, 2026

Public playtest: https://canvascontext.com/

Deployed executable **0.20.4**, rules artifact **0.12.0-rc.5-test**, clean source
`82c29ef776765fe980a9124547cde3d21ab28134`, tagged `frontier-rules-v0.20.4`.
The approved connected-prose rewrite now appears in the selected companion and
component projections. The mechanics fingerprint is identical to 0.20.3.
The prior immutable releases remain intact.

The incoming prose source passed all 318 tests. After release metadata changed,
46 release, content-graph, and publication tests passed, along with `npm run check`,
`npm run game:release:verify`, `git diff --check`, and the public Firebase build.
The first release verification rejected stale 0.20.3 evidence; that failure is
retained rather than rewriting the old release. The new rules artifact number
binds the new content and executable identity; it does not denote new mechanics.

Firebase Hosting reported a successful release to `canvascontext-9da05`.
Live checks matched all 46 served files against the build, loaded homepage
links, read the companion, started two-player desktop and five-player mobile
games, took an action, and exported game receipts without page errors.
The author bible, its source URL, Simulation Lab page, and internal provenance
page returned HTTP 404. This is browser and deployment evidence, not human
playtesting or subjective reader approval.

`live-verification.json` retains the deployed manifest and browser results.
`validation.tar.gz` retains validation logs, the original rejected release
check, deployment output, and the live verification script.

Component: Mandate 2038 publication. Intent: preserved.
Acceptance evidence: the linked adjacent records and archive.
Boundary effects: versioned content artifacts and public Firebase Hosting.
