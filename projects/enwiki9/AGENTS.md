# enwiki9 Agent Instructions

These instructions apply to `projects/enwiki9/`. Also obey the parent
`gamma/AGENTS.md`; this file is the nearest authority for enwiki9 work.

## Objective

Win with a constructive official enwik9 score:

```text
score <= 109,500,000 bytes
```

Continue through exact full-corpus replay, official accounting, clean
reproduction, and submission packaging. Forecasts, proxies, shadows, prefix
results, and archive-only gains are research evidence, not the objective.

No algorithm family is preferred or protected. Use, replace, or combine any
compressor, transform, model, parser, dictionary, retrieval system, ordering,
coder, teacher, search method, online learner, neural component, or hybrid that
has a credible path to a better legal counted score. A failed implementation
retires that implementation, not the broader idea.

## Optimize For Winning

Choose work by expected movement in the official score and the information it
will produce. Favor experiments that can reveal or capture enough net bytes to
matter after program cost, transfer loss, memory, and runtime.

- Start from the strongest relevant evidence, but use weaker compressors,
  oracles, synthetic cases, or alternate coders when they answer a useful
  discovery question cheaply.
- Attack the largest plausible sources of unmodeled information. Do not spend
  the search budget polishing a component whose best-case headroom cannot pay.
- Reuse existing traces, archives, binaries, receipts, and failure ledgers.
  Avoid rerunning a codec when a valid recorded stream can answer the question.
- Keep code size small when that improves the score, but do not reject a larger
  mechanism if measured archive savings pay for it with margin.
- Combine mechanisms when their gains are complementary. Keep them separate
  when isolation gives a faster or clearer decision.
- Stop parameter ladders after a decisive miss. Reopen a lane only with new
  information, a new representation, a new endpoint, or a materially different
  integration.
- Do not run a costly larger gate that is already known to miss unless its
  result resolves a specific decision that cannot be answered more cheaply.

Every substantive experiment should state, as briefly as possible:

```text
hypothesis
baseline and measured scope
expected byte leverage
promotion and kill conditions
result and next decision
```

These are decision aids, not a mandatory experiment shape. Skip steps when a
more direct test is sound.

## Freedom During Discovery

Discovery work may use noncausal oracles, embeddings, large teachers, hidden
labels, future context, uncounted research code, alternate orderings, external
models, or unshippable indexes. Label those dependencies honestly. Their job is
to locate information and suggest a constructive mechanism; they do not earn
submission credit.

The final candidate may also use sophisticated models, weights, tables, or
indexes when they are legal, shipped, counted, decoder-available, and fit the
official resource limits. Do not impose an artificial rule that the final
method must be tiny, symbolic, causal in one particular form, based on FX2, or
distilled from a teacher. Official rules and net score decide.

Do not require a fixed sequence such as proxy, shadow, prefix, and native for
every idea. Use the cheapest decisive evidence first, then move directly toward
constructive replay when the headroom justifies it.

## Start From Current State

Run commands from the repository root reported by
`git rev-parse --show-toplevel` unless a tool says otherwise. Do not encode a
machine-specific checkout path in commands, receipts, or continuation docs.
At the start of an enwiki9 work session, inspect:

```bash
sed -n '1,240p' projects/enwiki9/docs/status_receipt.md
pgrep -af 'run_with_rss_guard|projects/enwiki9/lib/driver.py|cmix21|enwiki9-heavy.lock'
```

Use these sources as needed rather than rereading all of them mechanically:

- `docs/status_receipt.json` for live gate and lock state;
- `ALGORITHMS.md` and `docs/research_register.md` for measured frontiers;
- `docs/takeover_runbook.md` for proof continuation;
- `CMIX21_LOCK_SAFE_QUEUE.md` only for the serialized cmix21 lane.

Do not regenerate status receipts merely because the repository was pulled.
Refresh them when underlying process, gate, certificate, or result state
changes and the handoff needs the new fact.

## Protect Active Proof Work

Use `/tmp/enwiki9-heavy.lock` for memory- or I/O-heavy compression jobs. Do not
mutate source, replace artifacts, or launch a competing heavy job underneath an
active proof gate. Bounded research may run concurrently only when it cannot
threaten the active job's memory, I/O, timing evidence, or inputs.

For an already-promoted proof sequence, preserve the candidate unchanged
between scopes. Use the lane's decider/controller to record terminal outcomes.
A tuned successor is a new candidate and needs its own identity.

## Evidence And Claims

Use precise evidence labels. At minimum distinguish:

- idea or design;
- proxy or oracle;
- causal shadow or trace replay;
- constructive prefix result;
- full-corpus official result.

Oracle and teacher results show available information, not realizable gain.
Qbits and loss estimates rank candidates; exact coder replay establishes saved
bytes. Cold-reset windows, opening prefixes, later slices, and cumulative runs
are different populations and must not silently substitute for one another.

If a trace, alignment, evaluator, decoder-state, or causality defect is found,
quarantine every dependent receipt and rebuild it from corrected inputs. A
favorable result from invalid instrumentation is not evidence.

Claim `10.95%` only when all are true:

```text
scope_bytes == 1,000,000,000
official_score_bytes <= 109,500,000
roundtrip_ok == true
```

Before treating a component as submission progress, count every byte required
to reproduce and decode it: program or source package, options, wrappers,
models, weights, tables, dictionaries, indexes, and configuration. Verify the
applicable official memory and runtime limits. Name decimal `10GB` and binary
`10GiB` distinctly.

Held-out populations, matched controls, deterministic replay, and frozen
selection are useful protections against overfitting. Apply them in proportion
to the claim. They are required before generalization claims, but they must not
become ceremony that delays a direct exact test.

## Status Reporting

Use `skills/enwiki9-status` for Hutter Prize status. Every user-facing status
update must state, compactly:

- the `109,500,000` target;
- the verified official full-1G score, or `unknown` when none exists;
- the best counted forecast and its signed distance from target;
- the active candidate's receipt-backed projection and distance, or `unknown`;
- the live gate's scope, progress, RSS guard state, and terminal status.

Label partial archive sizes and progress projections as provisional. Never call
them a current score, subtract them from the official distance, or let them
replace the last terminal receipt.

Live monitoring must be event-driven. Sample guards as often as needed for
safety, but do not publish unchanged polling output. Emit a routine update only
when progress crosses a five-percentage-point milestone. Emit immediately on a
terminal result, guard breach, material memory-boundary crossing, heavy-lock or
candidate-identity change, or an explicit user status request. Persist the last
emitted milestone so a restarted watcher does not repeat old updates.

## Record Decisions

Do not leave important state only in chat. Record decisive commands, hashes,
scope, byte results, failures, claim boundaries, and the next action in the
relevant receipt or strategy document. Preserve negative results that prevent
repeat work.

After changing receipts, candidate metadata, strategy documents, or generated
views, run:

```bash
python3 projects/enwiki9/tools/enwiki9_normalize_receipts.py
```

If normalization depends on an unavailable overlay, record that environment
failure without relabeling research evidence or mutating unrelated proof state.
