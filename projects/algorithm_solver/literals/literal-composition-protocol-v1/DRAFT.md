# Literal familiar assembly: task and two-arm protocol v1

Date: 2026-10-23. Status: task-definition draft for Codex/Claude cross-review;
not an execution freeze and not training or protected-scoring authorization.
Component: algorithm solver, literal autonomous composition (current goal 4a;
historical literal goal 3a). Intent and component boundaries are preserved.

## Authority and question

The owner's 2026-10-23 confirmation requires independent descriptions without
solution hints and separate, fully charged symbolic and trained arms under
identical correctness and information-access rules. This document fixes that
task before selecting either composer. It preserves [M1 and M2](../MILESTONES.md),
the [literal contract](../../contracts/literal_composition_goals_v1.json),
[goal aliases](../../contracts/algorithm_solver_goals_v2.json) and
[component charter](../../CATSCAN.md). Earlier
[typed-composer results](../../findings/completion-plan-128-v1/README.md) use a
different representation/population and cannot qualify this task.

Question: given one independently written description of a familiar problem,
can a frozen procedure emit its first correct complete program as selections
from one fixed literal vocabulary, without human steering, query-time
answer lookup, or autoregressive generation? The comparison measures symbolic
and trained approaches separately. Familiar-problem success is not unseen
semantic-variant or family generalization.

## Population and description commission

The eventual M2 denominator is the unchanged frozen admission500 population,
with JavaScript and Python qualified separately. A first development comparison
is restricted to the existing allowlisted 400 JavaScript development problems
(300 fit plus 100 consumed development validation). Those 400 problems are
familiar; a fresh description does not make their solutions unseen. No source,
statement, case or alias of the final 100 or protected 66 is opened or requested
by this protocol. Extending to the full 500 requires a separately authorized
execution freeze. A 400-problem experiment cannot establish M2's 400/500 gate.

Commissioning is prepared now; no descriptions are authored by the implementation
agents. The independent author and independent reviewer must not have built,
tuned or selected either composer or the representation candidate. Record their
identities, roles, relevant prior exposure and conflicts privately. They receive
only a custodian-provided specification packet for the allowed development IDs:
behavioral requirements, interface, valid input domain, output ordering,
mutation/alias, numerical/Unicode and complexity obligations, and public
examples. They do not receive implementation source, editorials, algorithms,
vocabularies, encodings, generated solutions, model predictions or failure logs.
The custodian audits the packet for solution hints before release.

Write exactly one primary scoring description per problem, expressing all
semantically necessary requirements in fresh wording. Preserve constraints
needed to identify correct behavior; do not turn a complete task into an
ambiguity test. Do not include solution steps, data-structure recommendations,
recurrences, pseudocode, source snippets, literal choices or algorithm names
that suggest a construction. Remove titles, source URLs and IDs from the
composer-visible text. A signature and type/schema declaration may be supplied
identically to both arms; it must not carry a source-specific name or lookup key.
The private mapping to the frozen problem is for scoring only.

The reviewer checks equivalence and completeness against the specification,
absence of solution hints and accidental source quotations, and lack of
protected-family overlap. Resolve defects before sealing without composer
feedback. Record any unresolvable authoring gap under the original problem ID;
do not substitute an easier problem or shrink the denominator. A defective
sealed description discovered after scoring is retained as a protocol defect,
reported with the original result, and blocks a qualification claim until a
new independently frozen evaluation. Do not silently drop or replace it.

Custodian seals the ordered description set, private ID mapping, author/reviewer
receipts, public-check bundle and independent judge contract with hashes and
timestamps. Only hashes, counts and metadata enter Git. Builders see no scoring
descriptions before both composer packages, public acceptance rules and budgets
are sealed. Authors/reviewers do not see predictions before description seal.
Scoring consumes the set once; afterward it is development data. Authoring and
review time are recorded as dataset construction cost, not hidden model compute.

## Common information and representation

Both builders receive the identical declared development bundle before their
implementation freeze: permitted familiar specifications, qualified source
variants, interfaces, public examples and the selected fixed literal dictionary.
All development texts must be identified; no sealed scoring descriptions or
independent scoring cases enter development or training. This permits offline
learning from familiar solutions and does not claim that learned weights cannot
memorize them. Source/alias family restrictions still apply. No external model,
corpus, service or download is added implicitly; any proposed pretrained
component needs a declared provenance/contamination audit and owner authority.

Select and hash one shared dictionary and exact flat-concatenation decoder
before fitting either arm. Its maximum is 256 nonempty literal entries, with
zero whole-solution entries. The same entry order and fixed-width packet codec
apply to both arms. All program bytes, helpers, constants, punctuation, names
and wrappers must come from emitted entry IDs; no raw-source escape, hidden
expansion, free renaming or task-specific helper body is permitted. Parameterized
macro/AST systems require a separately labeled future protocol.

The primary development comparison may use a frozen development dictionary
that does not meet M1; that yields mechanism evidence only. Full M2 qualification
requires retaining every M1 gate, without revising thresholds. Choosing a
composer cannot retroactively change the shared dictionary or test population.

At query time each arm gets only the identical authored description, declared
interface/types, public examples and its sealed deployment package. No problem
ID, family label, expected independent outputs, source file, stored complete
program/sequence, query-specific answer index, network call, sibling arm output,
or interactive clarification is available. A filesystem/network allowlist and
access receipt make this enforceable. Development data stays unmounted.

## Two composers and separate controls

| Arm | Allowed mechanism | Required separation |
| --- | --- | --- |
| S: symbolic | A frozen deterministic parser/planner or rule system builds one complete literal-ID proposal from the allowed input. | Rules and constants are counted, inspectable and audited for disguised per-problem answer bodies or complete stored sequences. |
| T: trained | A frozen non-autoregressive learned procedure predicts one complete literal-ID proposal from the same input and dictionary. | Weights, tokenizer, architecture and decoding procedure are sealed; training needs separate explicit owner go-ahead. |
| L: lookup control | Recognize the description and return a stored complete program/sequence from a declared finite table. | Table, recognizer and all storage/runtime are charged; score separately as recognition/lookup, never as autonomous composition. |

No architecture is chosen here. Before implementation execution, each composer
must declare exactly how it produces a proposal. Neither may emit successive
source tokens/literal IDs conditioned autoregressively on its preceding emitted
sequence. An encoder and simultaneous position predictions are potentially
eligible; next-token/source/literal generation is not. Symbolic construction
must also satisfy the rule. A fixed inspection/serialization pass over an
already chosen structure is not a free source-generation channel. Cross-review
must resolve eligibility before running, not after favorable output.

There is one primary proposal per query, committed before public checks. No
candidate search, reranking several complete programs, test-feedback repair,
resampling, second proposal or human edit contributes to the primary score.
Internal bounded analysis that constructs that one proposal is included in
runtime and must be specified. Any later search/repair experiment is a separate
arm, keeps its first proposal, and cannot replace the first-attempt metric.

L receives the same descriptions, public checker and query budget, but has an
explicit additional answer-table capability; label that exception prominently.
A known-ID retrieval ceiling may be reported as an additional oracle diagnostic,
never as L's description-recognition accuracy or either composer's score.
The offline canonical encoding of supplied source is only a representation
reference; it is not an autonomous control.

## Correctness, decisions and fixed pass rules

The harness stores the first literal-ID sequence and decoded source hash before
any check. Invalid entries, decode failure, syntax failure, absent output,
timeout and resource failure remain in the denominator. Public checks can
reject that proposal; they cannot edit it. The public checker, fail-closed
acceptance policy and resource limits are identical for S, T and L.
Expected independent outputs stay outside the sandbox and query process.

After all query outputs and accept/abstain decisions seal, an independent judge
checks the exact emitted source against the pinned specification and all
original independent cases, including effects, numerical behavior and required
complexity evidence. No substitution of the original source or its old receipt
for a new program is allowed. Exact-hash reuse of an existing receipt is allowed
only if the execution freeze explicitly pins the same contract/runtime/cases;
its reused status must be visible. Finite tests do not prove full correctness.

Report per arm and family: first-emission independent correctness; accepted and
independently correct answers; wrong acceptances; explicit abstentions; public
rejections; invalid/failed/time-limited attempts. The primary solved count is
accepted first proposals passing all independent checks. Correct but publicly
rejected proposals are reported separately and do not inflate accepted coverage.
A wrong acceptance is a publicly accepted proposal failing any independent
requirement. Missing evidence is unsolved, not correct.

Full M2 is met only if all of these hold on the authorized frozen 500:

- At least 400 distinct problems have an accepted, independently correct first
  proposal; no paraphrase or repeated timing request increases that count.
- Zero observed wrong acceptances, zero human edits and zero query-time
  autoregressive source or literal generation.
- At most 256 shared literal entries, median at most 32 and p95 at most 96
  selections over independently correct assemblies, at most 10% of their
  selection bits from single-character entries, zero whole-solution entries.
- Complete warm p50 at most 250 ms and p95 at most 1 s over all attempted queries,
  including failures and abstentions; all required storage and compute reported.

Report compactness over both independently correct first emissions and the
accepted-correct subset, explicitly named, plus failed-attempt costs and coverage.
An arm cannot use abstention to conceal poor representation coverage. M1
selection counts exclude the separately charged framing/controls; show actions
and selections separately. The 400-development comparison reports every gate
numerically but has no scaled substitute for the 500-population pass rule.

Compare S and T on the same queries with a full paired outcome table and a
95% paired interval for accepted-correct coverage difference. Freeze the interval
method before scoring, including its treatment of family dependence. These are
descriptive finite-population comparisons; no independent-request generalization
is inferred from correlated family samples. Report exact
paired discordance test and uncertainty for zero observed wrong acceptances
(with denominator accepted attempts). A descriptive difference is not a
superiority claim: require a two-sided 95% interval excluding zero before
claiming a coverage advantage, and state correctness, latency and storage
tradeoffs. Do not combine metrics into an unfrozen utility or select a winner
from timing alone. Neither the stronger arm nor agreement between agents
establishes protected confirmation, deployment readiness, novelty or M5.

## Complete charging and timing

Preserve raw per-query timestamps: input preprocessing, any retrieval, model or
symbolic prediction, sequence assembly/decoding, syntax/contract validation,
public-check execution and response serialization. Complete warm latency spans
all those stages through the answer/abstention decision. Record independent
post-query judging separately; do not let that judge influence the answer.

Freeze hardware, core/device allocation, numeric precision, batch size one,
input-length policy, cache policy, public checks, time/memory limits, seeds and
order before exposure. Warm-up uses separate permitted development queries;
never precompute/cache evaluation answers. Each timed primary query is the first
exposure to its scoring description. Interleave arms in a sealed balanced order
on the same dedicated resources, with cache isolation and no concurrent search
load; otherwise label latency exploratory and do not assert M2 timing. No silent
truncation; an over-budget input is a recorded failure. Cold startup, peak host
and device memory, and complete timing distributions are additional outputs.

Report byte-exact inventories and hashes for dictionary, packets (including
41-byte current framing, padding and controls), decoder, all parser/planner
code, grammar/rule tables, learned weights, tokenizer, runtime libraries and
lookup table. Show total deployable bytes, shared versus arm-specific bytes,
one-program cost and amortized cost over all attempted and solved programs.
No zero-byte learned knowledge, answer table or helper. Include original source
bytes and canonical encoding costs as labeled representation references.

Report offline dataset preparation, symbolic rule engineering, vocabulary
fitting, model fitting, hyperparameter/seed trials, discarded checkpoints,
validation, and final packaging separately: wall time, CPU/device time, peak
memory and artifact bytes, with unavailable quantities marked unknown. Training
steps, data exposure and failed runs are charged; the final checkpoint is not
the whole training cost. Do not claim equal offline compute merely because
query-time limits match. The execution freeze sets equal allowed query budgets
and a declared cap for each arm's offline search/training, including all trials.

## Before any execution

A separate versioned FREEZE.md must fill and hash the concrete allowlisted
population; independent author/reviewer/custodian receipts; shared dictionary;
S/T/L implementations; allowed development inventory; model provenance;
training method and exact budget; acceptance checker; independent judge;
hardware/runtime/core limits; warm-up/order; timeout policy; statistics script;
and artifact paths. Cross-review and push precede execution. Any unset field
blocks its dependent run; this draft provides no default training budget.

Explicit owner go-ahead remains required for training/learned scorers, any
final-heldout/protected opening, external commissioning contact not separately
authorized, human recruitment, source publication and deployment. The owner's
confirmation authorizes preparing this protocol and commissioning requirements;
it does not identify an author, supply sealed descriptions, or grant training.
Source licensing/provenance audit is a separate publication prerequisite; no
private source, description, case, dictionary or sequence is exported here.

No empirical prediction about S beating T is made without implementations.
Predeclared sanity expectations for the execution freeze are: independent
outputs cannot affect query decisions; decode and complete cost accounting
are reproducible; and lookup is never counted as composition. Failures of
those checks invalidate the comparison rather than qualifying another arm.
