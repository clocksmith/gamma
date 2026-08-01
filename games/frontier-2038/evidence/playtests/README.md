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

Every generated receipt and notes page records the exact rules version,
executable reference, and Git source commit. Use only components carrying the
same identity label.

Freeze the complete controlled-test kit only from a clean commit already
pushed to `origin/main`:

```bash
npm run physical-kit:freeze
```

The derived kit is written under `dist/physical-kit/`. Its manifest hashes the
rulebook, baseline component masters, source data, release identities, Session
A and Session B receipt templates, and test protocol. Deferred Tactics, secret
objectives, and Reserve Specialists are excluded.

Use `--type blind_playtest` only when players used the supplied rules and
components without designer answers.

`receipt.json` must conform to
`simulation/contracts/playtest-receipt.schema.json`. Copy the exact game,
ruleset, and playtest-kit identities from `versions/current.json` and its
manifest. Record mixed component revisions, rules deviations, and facilitator
interventions explicitly.

Never label a simulation or developer walkthrough as a blind playtest.
