# Track B handoff: qualified BITS targets (owner assignment 2026-11-12)

Owner assignment: Track B (qualified targets and expressibility) belongs to the
dot session; Track A (composer diagnostics and repair) stays with the session
that wrote this. Jupiter is the qualification target; Mars is the teacher host
if Jupiter's CLI cannot run the teacher. Training, evaluation and the encoder
download are NOT authorized; do not start them.

## State at handoff

- Plan frozen: [plan.json](plan.json), receipt [plan-receipt.json](plan-receipt.json)
  (`plan_sha256` c951e1d5…): 145 development_fit, 76 heldout_family,
  11 heldout_combination, 2 excluded_existing.
- Reviewed requirements: `contracts/bits_step1_reviewed_requirements_v1.json`
  (145 rows, 408 boundary cases; lcd:704 and lcd:1042 reviewed unsupported).
- Authorizations: `contracts/bits_step1_authorizations_v1.json` (dataset,
  Opus 5.5 teacher via `claude -p` with prompt sha 564bf6df…, held-out hashing).
- Teacher prompt: `contracts/bits_step1_teacher_prompt_v1.md` (no recipes).
- Driver: `python -m algsolve.synth.bits_step1 build --dataset … --authorizations …
  --plan … --reviewed-requirements … --prompt … --output <new dir>`; teacher in
  `algsolve/synth/bits_step1_teacher.py` (isolated CLI flags, per-call log).
- Dataset on Jupiter, verified: `~/gamma-data/bits/LeetCodeDataset-train.jsonl`;
  plan copy `~/gamma-data/bits/runs/plan-ade7c2f96.json`. Problem text, teacher
  inputs/outputs and builds stay outside the repository (dataset licence).
- Blocker: a one-call teacher smoke test on Jupiter (`make_generate_fn` →
  `claude -p --model claude-opus-5-5 …`, CLI 2.1.316) exited 1 with empty
  stderr. Unverified whether the CLI there is logged in or accepts the flags.

## Track B steps

1. Diagnose the Jupiter `claude -p` exit (login, flags, model access). If it
   cannot run there, run the teacher on Mars over the same public inputs and
   bind each proposal to the SHA-256 of its public input, so the Jupiter build
   replays recorded teacher output (the builder accepts "already authorized
   local teacher output"); record the CLI version and host per call.
2. Run `bits_step1 build` on Jupiter with the real sandbox (`judge=None`).
   Do not change the dataset, plan or reviewed requirements when candidates
   fail. Commit a qualified target manifest: summary, contract, counts of
   qualified, rejected, abstained, blocked and timed-out rows, artifact hashes
   (no problem text).
3. Expressibility report: separate representation failures (teacher
   abstentions with reasons, reviewed-unsupported rows) from construction
   failures (proposals rejected by public, independent, reviewed-boundary or
   probe stages), and record the operations, control flow, data structures and
   effects each accepted program uses. Alternative valid outputs need a
   separately versioned contract; do not relax this one.
4. Re-measure the Mars readiness receipt if any bound source changes.
