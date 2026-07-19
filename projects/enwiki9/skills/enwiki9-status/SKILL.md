---
name: enwiki9-status
description: Produce a source-bound Hutter Prize status for Gamma enwiki9, including verified full-corpus proof, closest counted forecast, active and retired candidates, measured gains, code-cost economics, live gate state, and quarantined evidence. Use when asked how close enwiki9 is to 10.95%, what the latest Hutter results or candidates are, what is running, whether a result is real versus forecast/shadow, or when recording a new decisive compression result.
---

# enwiki9 Status

Run the deterministic reporter from the Gamma repository root:

```bash
python3 projects/enwiki9/skills/enwiki9-status/scripts/report.py \
  --project-root projects/enwiki9
```

Use `--json-output PATH --markdown-output PATH` when a durable handoff is
needed. Use `--strict` before publishing or committing status; it rejects
missing required evidence, arithmetic drift, and invalid evidence tiers.

## Workflow

1. Read the nearest `AGENTS.md` files.
2. Inspect the process table and `/tmp/enwiki9-heavy.lock` for a live-status
   request. Refresh `docs/status_receipt.json` only when its underlying gate or
   process state changed.
3. Run the reporter. Treat its JSON as the normalized answer and its Markdown
   as the user-facing summary.
4. Report in this order: official proof, canonical counted forecast, active
   candidate, latest decisive evidence, next gate.
5. Never subtract a shadow/oracle gain from an official or constructive score.
6. End every report with `Continue toward the Hutter Prize` and the
   highest-ranked active candidate's evidence-producing next gate. After a
   verified win, replace that directive with proof preservation, reproduction,
   and submission packaging.

## Record New Evidence

After a decisive result, update `docs/hutter_frontier.json` in the same change
as its receipt. Follow [frontier-schema.md](references/frontier-schema.md).

- Bind every numeric claim to at least one source path.
- Normalize margin as `109500000 - score`; positive is below target.
- Preserve retired and quarantined rows instead of deleting them.
- Set `score_credit_bytes` to zero for proxy, oracle, and shadow evidence.
- Mark a full win only for exact `1,000,000,000` input bytes, complete program
  accounting, successful roundtrip, and score at or below `109,500,000`.
- Run the project receipt normalizer after changing receipts or generated views.

## Claim Language

Use these labels exactly: `idea`, `proxy`, `oracle`, `causal_shadow`,
`constructive_prefix`, `full_corpus_official`. A forecast can be counted and
still not be proof. A retired under-target forecast is historical evidence,
not the current distance to victory.
