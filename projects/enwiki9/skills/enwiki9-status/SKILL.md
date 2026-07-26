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
   Use `docs/hutter_run_ledger.json` when comparing the same candidate across
   scopes or corpus populations; do not reconstruct run history from prose.
4. Start with one compact score-status block: target in bytes and percent,
   verified official score in bytes and percent or `unknown`, best counted
   forecast in bytes and percent with signed distance, active candidate
   receipt-backed projection in bytes and percent with distance or `unknown`,
   then live gate scope, progress, RSS, and terminal state. Label every partial
   projection provisional.
5. Follow with candidate evidence, the latest decisive result, and next gate.
6. Never subtract a shadow/oracle gain from an official or constructive score.
7. End every report with `Continue toward the Hutter Prize` and the
   highest-ranked active candidate's evidence-producing next gate. After a
   verified win, replace that directive with proof preservation, reproduction,
   and submission packaging.

## Live Monitoring

The status skill is on demand; it does not require fixed-interval user updates.
Use `tools/enwiki9_gate_watch.py` for an active native gate. Its internal polls
are silent and its state file suppresses repeats.

- Emit routine progress only at five-percentage-point milestones.
- Emit immediately for completion, failure, an RSS guard breach, a configured
  memory-boundary crossing, candidate/PID identity drift, or an unexpected lock
  change.
- Answer an explicit user status request immediately without changing the next
  scheduled milestone.
- Never print an unchanged score block merely because another sample arrived.
- Recompute archive ceilings from receipt-bound debt, calibration, and counted
  program bytes. Do not transcribe a ceiling from chat.
- Compute Hutter percentages directly from the exact byte score and full
  1,000,000,000-byte corpus. Use seven digits after the decimal so a narrow
  target crossing remains visible.

## Record New Evidence

After a decisive result, update `docs/hutter_frontier.json` in the same change
as its receipt. Follow [frontier-schema.md](references/frontier-schema.md).

- Bind every numeric claim to at least one source path.
- Normalize margin as `108000000 - score`; positive is below target.
- Preserve retired and quarantined rows instead of deleting them.
- Set `score_credit_bytes` to zero for proxy, oracle, and shadow evidence.
- Mark a full win only for exact `1,000,000,000` input bytes, complete program
  accounting, successful roundtrip, and score at or below `108,000,000`.
- Run the project receipt normalizer after changing receipts or generated views.

## Claim Language

Use these labels exactly: `idea`, `proxy`, `oracle`, `causal_shadow`,
`constructive_prefix`, `full_corpus_official`. A forecast can be counted and
still not be proof. A retired under-target forecast is historical evidence,
not the current distance to victory.
