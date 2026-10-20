# Canonical corpus campaign v1

Private staging ledger for 2,354 eligible problems and 4,708 language entries.
This is coordination and evidence bookkeeping, not a solver. It never executes
candidate sources. Legacy v1 does not open independent test files; the explicit
v2 profile below host-scores already-approved test transcripts. Existing qualification
is recorded separately from canonical normalization completion.

## Verified starting inventory

- 2,354 approved Python selected-reference hashes verified against the existing
  catalog; 94 JavaScript source hashes verified against bilingual catalog v4.
- 89 JavaScript qualification receipts also match their historical pinned hashes.
  The five foundation entries lack individual historical receipt hashes in v4;
  their referenced qualified catalog is now hashed, without inventing an old pin.
- All 150 W002 B01–B06 incoming source files match the preserved Mac inventory.
  Their presence establishes no new execution or qualification result.
- 255 unique JavaScript candidate-covered IDs; 2,099 have no observed owned
  candidate. Raw third-party snapshot files do not count as owned candidates.
- 250 delivered reserved problem IDs (500 language entries) require explicit
  reconciliation. 100 W002 B07–B10 problem IDs (200 entries) await external
  delivery. Another 36 problem IDs (72 entries) are reserved through alias/family
  closure. Both languages are protected from competing claims.
- 1,968 unreserved problem IDs remain available; metadata is in
  `unreserved-preview.json`. This includes five existing qualified JS foundations.

`baseline-summary.json` is the immutable starting census. `ledger.json` is live:
use `status` for current claims/completion. `ledger-initial-incomplete-inventory.json`
is a preserved unsuccessful census attempt, before W001 unqualified original
candidates were included; it is not the live ledger.

## Resume and ownership

From this directory:

```sh
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign --ledger ledger.json status
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign --ledger ledger.json next --language javascript --limit 10
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign --ledger ledger.json show 0532:python
```

The coordinator currently owns ledger mutation. Workers retain their source,
contract and evidence paths and send them for integration. Existing claim token
files are named `claims-<owner-basename>.json`. Tokens are coordination identifiers,
not credentials. Claims do not expire automatically; release requires the owner
and token. After interruption, read the ledger and retained claim file and resume
that exact attempt. Do not start a competing attempt or regenerate the ledger.

Each mutation requires the current global `--revision`. File locking and atomic
replace prevent concurrent lost updates. A stale caller must reread status and
reassess; it may not silently retry a conflicting change.

```sh
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign --ledger ledger.json claim 0544:python --owner root-normalize-544 --revision 0
```

The command above is an example; 544 is already claimed. It must not be executed
again as fresh work. `--reconcile-delivered` permits only delivered reservations;
there is no flag to override awaiting delivery or alias reservations. Claiming a
family prevents other owners claiming that family in either language.

## Frozen attempt contract

Before executing an attempt, write a JSON contract with:

```json
{
  "schema": "algsolve.campaign-contract.v1",
  "entry": "0544:python",
  "source_sha256": "exact ledger source hash, or null when no original exists",
  "normalized_sha256": "exact candidate bytes hash",
  "independent_sets": ["copy the complete metadata list from the ledger entry"],
  "comparison": "unchanged",
  "interface": "exact-public-adapter",
  "public_tests": 1,
  "mutation_contract": "the reviewed problem-specific mutation rule",
  "alias_contract": "the reviewed problem-specific alias rule"
}
```

The placeholder strings are explanatory, not valid evidence. `independent_sets`
must be the unchanged list of objects containing uid/tests/sha256/path. Stage
copies the source candidate, contract and standard into content-addressed private
artifacts, records the attempt number and owner, and verifies original source
identity. It does not run any candidate or tests.

```sh
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign --ledger ledger.json stage 0544:python --owner root-normalize-544 --token TOKEN --revision REVISION --normalized candidate.py --contract contract.json --standard corpus_standard_v1.json
```

When the original source is an embedded approved Python reference, identity is
its corpus key, selected reference UID and code hash. The shared source JSONL is
not rewritten or copied into an attempt. The coordinator should retain originals
in the normal private research run as well.

## Completion evidence

`record --evidence bundle.json` accepts exactly three hash-bound receipt references
named `standard`, `execution`, and `review`. Each reference is an object with
absolute `path` and `sha256`. Each referenced JSON must contain:

- `schema: algsolve.campaign-evidence.v1`
- exact `entry`, `kind` (`standard`, `execution`, or `review`)
- exact `source_sha256`, `normalized_sha256`, `contract_sha256`
- `status: passed`
- nonempty `artifacts`: underlying artifact path/hash references

Additional required fields:

| Receipt | Required fields |
| --- | --- |
| standard | `standard_sha256`, `errors: []`, `idempotent: true` |
| execution | complete unchanged `independent_sets`; exact integer `independent_total`, `independent_passed`, `public_total`, `public_passed`; `mutation_passed: true`, `alias_passed: true`, `sandboxed: true`, `infrastructure_errors: 0`, `expected_outputs_in_sandbox: false` |
| review | nonempty `reviewer` distinct from attempt owner; `semantic_role_mapping_reviewed: true`, `complexity_reviewed: true`, `unresolved: []` |

Underlying artifact hashes are verified and snapshotted. All assigned independent
cases and public examples must pass: a domain-filtered subset cannot complete the
full entry. The raw domain disagreements and comparator differences remain
available for an explicit reviewed successor contract; this CLI cannot weaken
existing tests or mark them complete merely by changing counts.

This verifier enforces evidence structure and identity. It cannot prove that a
human/agent authored an honest receipt, that a role mapping is semantically right,
or that a claimed asymptotic bound is proved. The independent reviewer must inspect
the actual named source, judge outputs and standard-check receipts. An adapter from
older evidence schemas must retain their original receipts and explain the mapping;
never manufacture a passing receipt from a summary percentage.

Existing pilot attempts predate this ledger. Preserve their original source-freeze
contracts and failed attempts; do not misrepresent a later ledger snapshot as the
pre-execution freeze. Coordinator import requires a documented evidence adapter
and independent review before any completion is recorded.

## Failures and blockers

`fail` retains a failed evidence file and reason, marks the current attempt failed,
releases its claim and leaves the entry blocked. `release --blocked` preserves an
unfinished attempt as abandoned with its reason. Ordinary release returns pending.
No failed attempt is deleted or overwritten. A blocked item may be claimed for an
explicit new attempt, retaining the blocker and prior evidence until it passes.

```sh
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign --ledger ledger.json fail 0544:python --owner root-normalize-544 --token TOKEN --revision REVISION --evidence failed-receipt.json --reason 'Specific observed failure'
```

A changed reservation input file blocks all mutations until the coordinator
reconciles a new version of the census; silently updating reservation hashes is
not supported. New external delivery import likewise requires coordinator review,
source-hash verification and preservation of the previous reservation history.

## Validation and scope

```sh
python3 -m unittest -v test_campaign.py
```

13 tests cover successful evidence intake; stale source/artifact/revision rejection;
reservation and family ownership; failed/abandoned attempt retention; transaction
rollback; weakened test-set rejection; independent review; and the 2,354/4,708 census.
The census test skips when the private ledger is absent. No solve is claimed by
these software checks. No repository commit, public push, deployment, training,
protected scoring or independent candidate execution was performed by this ledger
subtask.

## Versioned statement-declared public comparison

Legacy v1 admission remains metadata-only. The opt-in v2 branch also reads already
approved host-only test transcripts and rescores their saved observations; it never
imports or executes candidate sources, opens unrelated test sets, or edits expected
values. Public order freedom comes from the pinned statement, not problem-name
inference or an author-supplied success count.

The coordinator explicitly registers `inputs.public_comparison_policy` as a
path/SHA256 reference to `algsolve.public-comparison-policy.v1`. The policy names
an approving coordinator distinct from the source author and pins each permitted
problem key, public packet and trusted binder/judge runtime. Policy-listed entries
must use v2 at both staging and recording; stripping extension fields cannot
downgrade them to the legacy path. Policy dependencies are snapshotted at staging
and must remain identical through completion.

A v2 contract declares `schema: algsolve.campaign-contract.v2`,
`comparison: statement-declared-public.v1`, `independent_comparison: unchanged`,
and the actual `source_author`. Its `public_comparison` descriptor binds mode,
policy, packet, statement, raw/bound public-test hashes and complete runtime hashes.
The verifier recomputes `bind(recover(problem))` using the trusted implementation.
Only default return-to-unordered_outer public changes are allowed; arguments,
expected arrays, multiplicity, types, explicit exact modes and independent
comparisons remain intact.

Execution receipts add the same descriptor and independent mode plus references
`semantic_qualification`, `qualification_freeze`, `host_tests`, and
`strict_predecessor`, all included in underlying artifacts. They retain
`strict_public_passed` separately. Complete independent groups must match their
original canonical hashes, and effective independent tests must equal the raw
tests exactly. Public raw/effective groups must match the pinned/bound packet.
Every chunk is checked for complete, contiguous coverage, clean bounded sandbox
flags, exact-integer unique result indices/completion, preserved call arguments,
no mutable input aliases, and judge-verifiable results. Stored counts/verdicts
must agree with host rescoring.

The independent review receipt additionally requires
`public_comparison_reviewed: true` and `public_comparison_sha256` equal to the
canonical descriptor hash. The source author cannot provide this review. Existing
source-standard, interface, semantic-role, complexity and full independent-case
gates remain required. Historical strict failures stay immutable; a semantic
qualification is a separate versioned result and must never be labeled unchanged
or presented as a repaired historical score.

Portable tests in `tests/test_campaign_public_admission.py` use only synthetic
fixtures from `tests/campaign_public_fixture.py`; the existing legacy campaign
tests remain separate. Artifact hashes bind evidence consistency, not honesty or
mathematical correctness; coordinator provenance checks and independent review
remain mandatory. Private transcript test data must not be exported publicly.

## Source selection before payload decoding

The shared source verifier selects the exact first-field corpus key before JSON decoding. It preserves the existing selected reference UID and code hash checks, rejects duplicate selected records or object fields, and fails closed when the selected identity is absent or unsupported. Streaming still reads raw file bytes; this is a pre-decode boundary, not a zero-filesystem-access claim.

Preparation and replay use the reviewed scoped reader with explicit claimed keys/UIDs and complete raw/canonical record pins. Independent-test loading uses one exact approved UID/path, rejects symlinks, checks the raw hash before decoding, and then verifies the unchanged canonical case list. New executions bind the reader activation and measured runtime identities before and after execution. Historical broad-decoding incidents, failed attempts and evidence remain immutable; subsequent safe intake cannot retroactively establish historical source nonaccess or model-context non-exposure.

## Version 3: explicit exact-integer interfaces

The `exact_integer_policy` input authorizes only the pinned LC670 JavaScript uint20 Number/BigInt profile. `uint64_bool_policy` independently authorizes the pinned LC633 Python/JavaScript uint64-to-strict-boolean profile. Policies bind language, source, standard, numeric domain, runtime contract, technical review, prior failures, measured toolchain and raw evidence. They do not modify earlier Python670 completion or silently widen a legacy interface.

Admission performs host-only replay of saved raw observations against unchanged case/expected/comparison identities. It checks exact decimal representation, strict runtime labels and booleans, complete test/control coverage, input preservation, sandbox status, and measured executable/module/link identities. Candidate code, codecs and runner artifacts are never imported by admission. Exhaustion in the bounded633factorization algorithm remains an error; no total uint64 completion guarantee is implied.

A source author cannot approve or independently review their own candidate. Named identities must be nonempty strings, and policy-listed entries cannot downgrade by stripping alternate-interface fields. The actual ledger policy snapshot must be enumerated in execution artifacts even when its bytes equal an original policy at another path. Historical failures and rejected wrappers stay preserved. The separately named interfaces qualify consumed development normalization; they establish neither autonomous solving nor protected generalization.

The separate `inputs.uint1024_policy` admits only `0738:javascript`, using
`lc738-uint1024-number-bigint-v1`. Here “uint1024” means at most **1024 decimal
digits**, with values from 0 through 10^1024−1. It does not mean a 1024-bit integer.
The original problem domain remains 0..10^9. The frozen 114 development cases
include 85 official-domain and 29 extended cases; all pass. These are consumed
development cases, not fresh generalization evidence.

A new outer dispatcher delegates every existing profile to the unchanged
633/670 dispatcher. The 633 validator and dispatcher, 670 validator/toolchain
helper, and prior policies retain their exact bytes and identities. The only
changes to `corpus_campaign.py` are its two dispatcher imports. The 738 policy
pins the resulting whole module, every gate dependency, and a historical reader
snapshot. Admission proves the exact two-import transformation and equal
`verify_source` ASTs. The old activation and postverification remain historical
whole-module evidence; they are not relabeled as the new module's identity.
Unchanged scoped helper files continue to be verified against current bytes.

The gate parses and scores host evidence; it never imports or executes candidate,
author codec, harness, runner, or historical reader code. It requires the separate
post-run independent review, frozen source and test contracts, all 114 raw named
transcripts, 114 raw sandbox controls, 30 identified host controls, and the measured
runtime and reader evidence. Every sandbox receipt binds before/after runtime
verification. Raw canonical decimal envelopes reconstruct exact integers before
unchanged host comparison; Number/BigInt boundaries, strict index/status types,
mutation and primitive alias observations fail closed. The pinned runner's
`sandbox_ok` comes from `SandboxResult.ok`, including the output-limit flag.
The gate explicitly checks that evidence; it does not manufacture a missing flag.
Measured executable/library/module identities are checked again at intake, with
no claim of a complete dynamic or kernel/CPU closure.

The preserved Number attempt remains 109/114. The separately blocked uint20
attempt remains 92/92 executed, 22 unexecuted, with its raw index preserved.
Completed Python738 is unchanged. Neither a stripped legacy contract nor a
combined comparison/runtime profile can bypass the 738 coordinator requirement.
Stage snapshots the approved policy and all dependent evidence; record checks
that authority and replays the observations. Synthetic tests use temporary
policies/ledgers only. The supplied policy proposal is pending; root approval,
independent admission evidence, installation and intake remain separate actions.

## Exact 868 admission and explicit 738 compatibility transition

The separate `inputs.integer868_policy` admits only `0868:javascript` under
`exact-public-spelling:lc868-uint1024-to-small-number.v1`. The input is a
nonnegative integer with at most 1024 decimal digits; the result is a small exact
Number. This is the pinned source and runtime interface, not authorization for
arbitrary large-integer programs. Its saved qualification contains all 68
unchanged cases per language: 52 official-domain and 16 extended cases. The gate
replays the saved observations and 77 controls without executing candidates.
Only JavaScript admission changes; the completed Python entry stays unchanged.

The new outer dispatcher preserves the prior 633/670/738 and ordinary admission
routes. The shared campaign module changes only its two dispatcher imports;
its source-selection function and scoped helper identities remain unchanged.
The explicit 738 compatibility transition preserves its historical policy and
changes only the approved admission-module identities and transition reference.
Its source, numeric domain, comparisons, scores and prior evidence are retained.
Old whole-module identities remain historical evidence and are not relabeled.

Installation requires finished old-identity executions and intake, a pinned
readiness record, preserved module/ledger snapshots, and verification of the
installed closure. The coordinator changes the policies and reader activation
together, then independently verifies the installed state before admission.
Execution artifacts must name the actual content-addressed policy snapshot;
byte equality to a policy at another path is insufficient. Prior failed Number
transport, rejected wrapper attempts and reference-access incidents remain
preserved. These consumed development results establish neither protected
nonaccess nor autonomous composition or semantic-variant generalization.
