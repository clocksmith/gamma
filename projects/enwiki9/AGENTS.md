# enwiki9 Agent Instructions

These instructions apply to the entire `projects/enwiki9/` subtree. Also obey
the parent `gamma/AGENTS.md`; when instructions conflict, this file is the
nearest project-specific authority for enwiki9 compression work.

## Prime Objective

Keep working toward a full enwik9 constructive official score:

```text
score <= 109,500,000 bytes
```

Do not stop at forecasts, prefix wins, shadow wins, or archive-only
improvements. After the target is hit, continue through official accounting,
clean reproduction, submission packaging, and further score reduction without
weakening the proof boundary.

Do not declare the target impossible, do not give up at the current frontier,
and do not treat a failed lane as the end of the search. Convert every blocker
into one of these concrete artifacts:

- a recorded terminal gate receipt;
- a lower-memory or lower-cost candidate;
- a regression table showing where bytes were lost;
- a new deterministic feature, route, parser, coder, or mixer to test;
- a retired-lane note with the measured reason it no longer deserves compute.

Progress is measured in verified byte movement toward the target, reduced
uncertainty, and stronger proof boundaries. Prefer the action with the clearest
expected byte leverage per added code/table byte and per guarded run.

## Start Every enwiki9 Work Session From Receipts

Run commands from `/home/clocksmith/deco/gamma` unless a tool states otherwise.

First refresh or inspect the live operator receipt:

```bash
python3 projects/enwiki9/tools/enwiki9_status_receipt.py
```

Read these before acting:

- `docs/status_receipt.md` and `docs/status_receipt.json` for active gate,
  lock state, operator action, and next command.
- `ALGORITHMS.md` for the current target strategy register.
- `PROJECT_ORGANIZATION.md` for source-of-truth routing.
- `docs/takeover_runbook.md` for continuation procedure.
- `CMIX21_LOCK_SAFE_QUEUE.md` for the serialized cmix21 gate queue.

Before reporting live work, inspect real process state:

```bash
pgrep -af 'run_with_rss_guard|projects/enwiki9/lib/driver.py|cmix21|enwiki9-heavy.lock'
```

If a scorer or heavy lock is active, do not launch another compression gate and
do not mutate active candidate source. Continue only read-only audits, receipt
normalization, strategy notes, shadow analysis, or documentation cleanup.

## Perpetual Execution Loop

Use `docs/status_receipt.json` as the active handoff, not memory or chat
history.

If no scorer is active and the receipt says `safe_to_launch_heavy_gate: true`
with a `next_gate_command`, launch exactly that guarded command. When a gate
finishes, use `tools/cmix21_gate_decider.py` and only its printed terminal
commands to record pass, RSS failure, roundtrip failure, determinism failure, or
promotion. Do not hand-compose promotion commands.

The cmix21 proof lane is serialized:

```text
exact prefix gate
  -> larger exact prefix gate
  -> 100M guarded replay
  -> 1G guarded replay
  -> official accounting audit
```

Do not retune between gates unless the current gate reaches a terminal failure.
If a gate passes, promote the same package unchanged. If RSS fails, record the
failure and package the smallest justified lower-memory cut. If roundtrip or
determinism fails, do not promote.

When no safe heavy gate is available, keep moving horizontally:

- mine existing receipts for block-local wins, regressions, and abstention
  opportunities;
- improve shadow-coder accounting, route selection, and feature attribution;
- package the smallest deterministic paying component from a positive shadow
  result;
- update strategy files so the next operator has a sharper next command;
- write probes that are cheap, causal, deterministic, byte-counted, and easy to
  retire.

## Novel Algorithm Strategy

The primary novel strategy is SRSTC / streaming self-referential semantic
retrieval. Treat the strongest target-closing SRSTC receipt as an integration
target only after block regressions are removed or routed around. Treat the
best zero-regression SRSTC receipt as the safe fallback floor.

Think horizontally and recombine aggressively. The project should synthesize
ideas from compression, MDL, online learning, retrieval, language modeling,
information theory, grammar induction, automata, parsing, indexing, error
correction, search, and test-time routing. A new idea is useful only if it can
be turned into a causal deterministic mechanism whose bytes are counted and
whose gains can be replayed.

When using current research or outside ideas, reconstruct the mechanism in
project terms instead of copying claims. Prefer primary sources, derive the
compression implication, then encode the distilled rule, feature, router, or
coder in `ALGORITHMS.md`, `docs/research_register.md`, or a receipt-backed
tool. If the idea needs unavailable training data, hidden model weights, or
uncounted payload bytes, reduce it to a tiny deterministic rule or reject it.

Use all other novel lanes as components or probes until receipts justify
promotion:

- residual/SSE patch compilers need exact held-out shadow bytes, counted tables,
  and full-coverage receipts;
- FX2-SC, CR-SSE, WikiFSM, schema tries, MWCC, I-SSA, and embedding-teacher
  work must be causal, deterministic, counted, and replay-backed before any
  target claim;
- forecast and attribution evidence may choose the next experiment, but never
  proves the score.

Promote a novel component only when net bytes saved exceed all added
code/table/package bytes and an exact replay proves decode, roundtrip,
determinism, RSS, and accounting.

Every novel probe should answer:

```text
what byte pattern does this model better?
what causal state is available to decoder and encoder?
what bytes does the implementation add?
what exact scope was measured?
which blocks improve, regress, or need abstention?
how does it integrate with cmix21, fx2, SRSTC, residual/SSE, or a sidecar?
```

Do not merely add knobs. Prefer mechanisms that explain a class of missed
probability mass, route around regressions, or combine two previously separate
signals into a smaller counted representation.

## Claim Boundary

A `10.95%` claim is allowed only when all of these are true:

```text
scope_bytes == 1,000,000,000
official_score_bytes <= 109,500,000
roundtrip_ok == true
```

Prefix rows prove only same-scope upper bounds. Shadow rows prove only shadow
model savings. Forecast rows prove no constructive bound. Always name the
evidence level and receipt path for score claims.

Count every byte needed for reproduction: wrappers, options, static
dictionaries, tables, build scripts, model descriptors, decompressor
configuration, and source packages. Name memory units explicitly; distinguish
the local binary `10GiB` guard from decimal `10GB` accounting risk.

## Required Maintenance

After changing receipts, candidate metadata, strategy docs, or generated views,
run:

```bash
python3 projects/enwiki9/tools/enwiki9_normalize_receipts.py
```

Do not hide state in chat. Encode next actions, blockers, proof status, and
claim boundaries in the relevant repository artifacts.

## No Time Estimates

Do not estimate work in hours, days, weeks, or any other time unit. Describe the
specific gate, file, receipt, function, or blocker instead.
