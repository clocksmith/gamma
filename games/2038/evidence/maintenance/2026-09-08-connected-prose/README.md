# Connected-prose pass — September 8, 2026

Applied the user's approved engineering-firm cadence to the primer, all four
Era overviews, named vignettes, four endings, and related Headline descriptions
in `world.md`. Added the approved passage to Progress and recorded the voice in
the existing writing contract. The named vignettes now retain their concepts
and Era placement with revised prose; the prior pass's verbatim-preservation
claim describes that earlier pass only.

No component mechanics, IDs, effects, costs, or Era placements changed. The
mechanics fingerprint matches executable 0.20.3. The first focused check failed
on a regex requiring “cognitive-donor” to precede “sleeping brains”; both concepts
remain present and are now checked independently. Its failed output is retained.

Final validation: 63 focused tests and all 318 full-suite tests passed;
`npm run check` and `git diff --check` passed. Chrome verified the generated
companion and posthumous-work card at 1440 and 390 pixels without horizontal
overflow or page errors; the card also had no vertical overflow. These checks
establish rendering and content consistency, not subjective reader approval.

`validation.tar.gz` retains source/output hashes, logs, and screenshots.
Read `dist/docs/world-and-institutions.md` for the generated companion.
This pass created no new immutable release and performed no deployment.
