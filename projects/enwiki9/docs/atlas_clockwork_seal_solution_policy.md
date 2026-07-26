# Atlas-Clockwork Seal Solution and Version Policy

Status: canonical policy for mathematical examination versions, submissions,
reviews, errata, and Seal-transfer decisions.

## 1. Separation of artifacts

The following are distinct artifacts and must never be silently merged:

1. **Problem version:** the exact mathematical text presented to a solver.
2. **Raw submission:** the solver's exact answer as received.
3. **Mathematical review:** the organizer's assessment of correctness.
4. **Transfer review:** whether the result satisfies a private Seal antecedent.
5. **Canonical exposition:** an optional edited proof prepared after review.

Editorial improvements belong in a canonical exposition or a later problem
version. They must not overwrite a raw submission.

## 2. Submission intake

Every submission receives a stable identifier of the form:

```text
ACS-<problem>-<UTC basic timestamp>-<submission hash prefix>
```

The intake receipt must record:

- UTC receipt time in RFC 3339 form;
- solver identity or `unattributed`;
- problem identifier;
- exact problem-version label;
- SHA-256 of the exact problem text;
- path and SHA-256 of the raw submission;
- source-bound Gamma commit when known;
- intake and review status;
- mathematical outcome;
- Seal-transfer outcome.

The raw submission becomes immutable when its receipt is created. A corrected
solver answer is a new submission with a new identifier, timestamp, and hash.

## 3. Timestamping and priority

UTC plus SHA-256 is the canonical local receipt. A Git commit records repository
history but is not the sole provenance mechanism.

For public priority or a released examination:

1. Publish the problem-version and submission hashes.
2. Create a signed Git tag or immutable GitHub release.
3. Preserve any external timestamp or release identifier in the receipt.

Changing whitespace changes the artifact hash and therefore creates a different
artifact, even when the mathematics appears unchanged.

## 4. Problem-set versions

Problem versions use labels such as:

```text
ACS-MATH-DRAFT-1
ACS-MATH-1
ACS-MATH-2
```

`DRAFT` versions may be reviewed, but any exact draft given to a solver is
frozen for that submission by its hash.

A non-draft version is immutable after publication. Changes are handled as
follows:

- Typographical clarification with no semantic effect: publish an erratum
  linked to the original version.
- Changed quantifier, hypothesis, conclusion, bound, grading condition, or
  computational model: issue a new version.
- Private Seal antecedent or adapter change: issue a new Seal binding version;
  do not silently change the public theorem's claimed transfer.

Every new version must have a changelog entry, exact hash, release state, and
independent binding decision.

## 5. Grading

A submission is graded only against the exact problem hash in its receipt.

Allowed mathematical outcomes are:

```text
RECEIVED
UNDER_REVIEW
COMPLETE
INCOMPLETE
CORRECT_COUNTEREXAMPLE
INCORRECT
SUPERSEDED
```

When a problem explicitly permits proof or disproof, a rigorous counterexample
is a complete mathematical result. When a required assertion is false but the
problem does not permit disproof, the review records the counterexample and a
specification defect; it must not pretend the false assertion was proved.

`COMPLETE` is a mathematical judgment only. It does not imply a Seal pass,
compression gain, target score, or prize eligibility.

## 6. Errata and evolution

An error discovered by a solution must be handled fail-closed:

1. Preserve the original problem and submission.
2. Record the exact defect in the review.
3. Add an erratum to the version ledger.
4. Decide whether the correction is semantic.
5. If semantic, create a new problem version.
6. Rebuild or re-audit every affected private binding.
7. Grade the original submission under the original text.

Historical versions and their solutions remain available for audit. They are
never rewritten to make later reasoning appear contemporaneous.

## 7. Seal transfer

Each mathematically accepted solution receives an independent transfer outcome:

```text
NO_ROUTE
ALGEBRA_ONLY
ANTECEDENT_PARTIAL
ANTECEDENT_SATISFIED
TRANSFER_VERIFIED
BOUND_PASS
```

The progression is:

```text
mathematical result
  -> extraction memorandum
  -> target-bearing antecedent
  -> frozen application map
  -> exact adapter and verifier
  -> score, reversibility, runtime, and memory receipts
  -> Seal binding decision
```

No mathematical elegance, asymptotic existence theorem, oracle saving, proxy
score, or projected score receives Seal credit without the required
constructive transfer artifacts.

For Problem D specifically, parity separation alone is `ALGEBRA_ONLY`.
Binding requires at least a low-rank energy on the hidden application,
constructive bounded reconstruction, complete coding accounting, and eligible
resource receipts.

## 7.1 Post-solution extraction

After a problem is mathematically `COMPLETE`, do not enlarge or replace it
merely because its hidden antecedent is absent. First produce an extraction
memorandum containing:

1. The exact theorem conclusions now available to the organizer.
2. The canonical finite witness or construction licensed by those conclusions.
3. Every hidden antecedent not supplied by the theorem.
4. The exact experiment or certificate that can establish each antecedent.
5. A fail-closed transfer status and zero score credit until all antecedents
   are satisfied.

A new public problem is justified only when transfer is blocked by a genuinely
unknown mathematical proposition whose proof would discharge a frozen
antecedent. Missing data, missing implementation, negative compression,
unmeasured runtime, unavailable teachers, and absent full-corpus receipts are
organizer obligations, not new pencil-and-paper questions.

The organizer must never ask a solver to rediscover a compressor by disguising
an empirical search problem as a theorem. A target-bearing route must identify
the hidden finite instance and prove the conditional reduction before solver
distribution.

## 8. Disclosure

The public problem may be distributed only when its applicable Seal policy
allows distribution. Raw solutions may remain private during an active
examination, but their hashes and receipt times may be published for priority.

Organizer reviews, private antecedents, adapters, hidden instances, and transfer
manifests are not solver instructions unless explicitly released.

## 9. Canonical storage

New material should use:

```text
docs/atlas_clockwork_seal/
  CHANGELOG.md
  versions/<version>/
  solutions/<problem>/<submission-id>/
    submission.md
    receipt.json
    review.md
```

Existing flat files remain valid when a receipt records their exact path and
hash. They may be moved only in a source-history-preserving change; their
contents must not be altered during migration.

## 10. Current policy application

The first registered artifact under this policy is the Problem D solution
received on 2026-07-26. It is bound to the exact
`atlas_clockwork_seal_problem_set.md` hash recorded in its receipt.

Its mathematical status is `COMPLETE` with two specification corrections. Its
Seal-transfer status is `ALGEBRA_ONLY`, and it receives zero compression-score
credit.

The combined Problems A-C submission is also registered. Problems A and B are
`COMPLETE`; Problem C is `COMPLETE` under the solver-confirmed C1
qualification. Their transfer states remain `ANTECEDENT_PARTIAL`,
`ALGEBRA_ONLY`, and `ANTECEDENT_PARTIAL`, respectively.
