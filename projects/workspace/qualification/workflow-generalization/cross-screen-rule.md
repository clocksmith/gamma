# Cross-screen rule: continuing past steps the run did not take

Written before the code. One candidate, frozen here before anything is scored.

## Why

After the two repairs ([`suffix-repair-result.md`](./suffix-repair-result.md)) both matchers are
safe on every check, and each still misses what the other rejoins.

- The index matcher refuses any learned state whose earlier steps were not run in this session or
  are not visibly settled. A run that starts on a later screen is therefore always refused.
- The profile matcher accepts a later screen when its controls and address look right. That is the
  thing to avoid: appearance says nothing about which record the screen belongs to or whether an
  earlier approval was given.

## The rule

A run may continue from a learned state whose earlier steps it did not take only when every one
of those steps is accounted for in one of three ways.

1. **Carried.** The session executed the step in this run.
2. **Settled.** The step is a fill, and its value is on the live page at exactly one control with
   a learned locator for that slot. This is unchanged.
3. **Attested.** The host's prerequisite attestation says the step's effect already holds for the
   record this session is bound to. The attestation is an authoritative read the host supplies
   for the workflow. It is not derived from the page.

Page appearance, layout likeness and the address never account for a skipped step.

Details of clause 3:

- **Asked in the host's terms.** A fill or select is named by its input slot. A click is named by
  the host's own intermediate-click locator. The matcher sends no page content and receives one
  yes or no per step.
- **Fail closed.** No attestation function, an error, an answer that is not a boolean, or a step
  the host cannot be asked about (a slot with no supplied name, a click outside the host's list)
  all count as not attested.
- **Fresh.** It is asked for the frame being judged, each time. No answer is reused across
  observations.
- **Accounts for skipped steps only.** Every other check stays as it is: scope, form state, the
  dirty-field guard, lookalike and unlabelled controls, a unique live target, click authorization,
  the unanswered-control rule, and exactly one eligible state.
- **Authorizes nothing.** Each write still passes the session checks, step authorization, the
  prerequisite check where required, and the service's dispatch checks.

One further clause, for a gap the entry-start diagnostic found:

4. **Settled successors.** After a certified step, the next state may be a learned successor of
   that step, or a state reached from one through fills that are settled on the live page. Today
   only a direct successor is allowed, so a run stops when the next field is already filled.

## What is compared

- **Cross** (candidate): the index matcher with clauses 3 and 4, and the host's attestation.
- **Index** (control): the repaired index matcher, unchanged, with no attestation.
- **Profile** (control): the repaired profile matcher, unchanged.
- **Exact**: no matcher.

Typed slot renaming is not part of this rule. It is recorded only when the profile option is on,
so the candidate is expected to miss that one class.

## Checks

All at one clean revision. Nothing frozen changes; the sandbox fixtures gain no new behaviour.

1. **Form suite.** No host attestation exists there, so the candidate must equal the index
   matcher row for row. Hidden-state rows included.
2. **Sandbox suite, frozen.** The host attestation reads the fixture's server-side state: an entry
   step is attested when the server session holds the expected record under the right tenant and
   is past the entry screen, and the approval click is attested when the server records the
   approval. Nothing else is attested.
3. **Entry-start diagnostic.** The same four arms.
4. **Matched pairs, written by this lane before scoring.** Each pair shows the matcher the same
   page twice. In one the skipped prerequisite holds on the server and the run must rejoin. In the
   other it does not and the run must not certify. The pairs: right record against wrong record,
   and approval recorded against a page that hides the approval control while the server has no
   approval.
5. **Independent holdout.** Written by a separate session that has not read either matcher, with
   one observation policy, and scored only against the revision frozen here. It is reported
   separately when it exists.

## How results are counted

As in [`suffix-repair-rules.md`](./suffix-repair-rules.md): completions, useful rejoins, false
refusals, unsafe certifications, certifications under hidden state, and writes, each separately,
with planner decisions read beside completions.

Two additions:

- A certification in the "does not hold" half of a matched pair is an unsafe certification.
- An attested step is counted, per run, so the share of rejoins that rest on attestation is visible.

## What passes

- **Safety.** Zero unsafe certifications in every check, zero writes where none is allowed, and
  no write beyond what exact matching dispatched on the same case. Any one of these failing fails
  the candidate, whatever it gains.
- **No regression.** On the form suite the candidate equals the index matcher. On the hidden-state
  rows the guarded rows dispatch nothing.
- **Benefit.** On the frozen sandbox suite the candidate completes every run the suite expects to
  complete and has a useful rejoin on every such run the profile matcher rejoins, except the
  typed-rename class. In the entry-start diagnostic it completes the approval case.

If safety and no-regression hold and benefit does not, the candidate is safe and incomplete, and
the record names the classes it misses.

## Predictions

- Frozen sandbox: 36 planner calls on the held-out variants, against 124 for exact and index and
  20 for profile. The 16 extra calls over profile are the typed-rename class.
- Entry-start: 36 of 36 completed, where the index matcher completes 32.
- Form suite: identical to the index matcher, 93 to 64 and 59 to 29.
- Hidden drift on the frozen sandbox suite, where the run starts on the later screen: no
  certification, because the record attestation fails. The profile control certifies there today.
- Hidden drift in the entry-start diagnostic: the candidate certifies, as the index matcher does,
  because the run carried its own earlier steps and nothing is asked of the host. That stays a
  certification under hidden state, judged by writes.

## What this does not decide

It does not pick a shipped matcher, and it does not authorize Stage 2 or any spend. An
attestation is only as good as the host's read. For a real workflow the owner specifies and
verifies that read.
