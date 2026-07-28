# Playtest Records

Store one directory per session:

```text
YYYY-MM-DD-player-count-seed/
  receipt.json
  notes.md
  scores.json
```

Create a correctly attributed session before play:

```bash
npm run playtest:new -- \
  --players 4 \
  --seed four-player-baseline-01 \
  --type facilitated_playtest
```

Use `--type blind_playtest` only when players used the supplied rules and
components without designer answers.

`receipt.json` must conform to
`simulation/contracts/playtest-receipt.schema.json`. Copy the exact game,
ruleset, and playtest-kit identities from `versions/current.json` and its
manifest. Record mixed component revisions, rules deviations, and facilitator
interventions explicitly.

Never label a simulation or developer walkthrough as a blind playtest.
