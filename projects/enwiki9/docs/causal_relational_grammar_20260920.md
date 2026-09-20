# Causal relational grammar: first native binding comparison

The user-selected research direction is persistent relational argument binding
across structure and content histories, with one existing FX2 coding sequence.
The target remains 96,000,000 complete bytes, 95,000,000 stretch; verified full
corpus score is unknown. The earlier split and retraining losses remain intact.

The [prospective design](../operations/adaptive/experiments/fx2_relational_binding_design_q0_v1.json)
precedes implementation. The [source-bound experiment](../operations/adaptive/experiments/fx2_relational_binding250k_q0_v1.json)
then freezes one implementation, zero tuning trials, three populations and all
five arms. Its plan corrects the initial design's bookkeeping expectation:
zero assumed gross saving minus the 65,536-byte maximum package allowance is
-65,536 expected net bytes, not a measured prediction. No gain is assumed.

The pure [predictor](../lib/predictors/causal_relational_v1.hpp) stores complete
raw word spellings, their exact modeled-byte spellings and completion coordinates.
Separate FIFO reservoirs hold at most 64 title words and 64 body words; each
word is bounded at 64 raw and 32 modeled bytes. A word enters only after its
complete inverse emission and a decoded delimiter. The unchanged WRT inverse
supplies the raw coordinates. Unrecognized markup and bytes remain literal.

Every 4096 modeled bytes, each role selects at most four recent donor words
paired with older, distinct spellings of equal modeled length. The complete
inventory stays fixed through that epoch. Title words predict subsequent body
words; body words predict later link-target words after a decoded `[[` marker.
This is a depth-one exact-spelling transducer, not a full entity recognizer,
recursive template learner, or edited-copy model. These limitations define the
first test rather than replacing the broader proposed grammar.

The latent variable is donor identity. A decoder-known nonletter boundary starts
an attempted mention; each donor follows its stored spelling until a mismatch
or its end, then emits the parent distribution. At active bits the emission is
half parent and half a nearly deterministic copy prediction. This guarantees
nonzero literal probability. Bayesian donor weights persist between mentions
in S; I resets them to uniform at each mention. A separate P/Q sequence mixture
resets only at the declared epoch boundary. All arithmetic coding and original
FX2 predictor updates remain unchanged; no models are trained.

P returns original probabilities. K executes the same bookkeeping as S but
returns P. W uses the paired older distinct donor words. Permuting equally
weighted donor IDs would leave a marginal unchanged and is not used as a
negative control. Slots, candidate pairs, structural bounds and mention schedule
are common across I/S/W; posterior values and realized copy survival can differ.

Q48 posterior weights use 128-bit intermediate products and deterministic
largest-remainder rounding, with one quantum per state. Output is rounded to
native 16-bit probabilities. Exact-rational synthetic tests check 300 generated
updates and bound each state's one-update error by 4/Q. A constructed repeated
donor fixture demonstrates benefit from the actual fixed-point persistent kernel.
Further tests check introduced-state equality, bounded storage, bookkeeping
identity and delayed two-byte WRT emissions under undefined-behavior sanitization.
Three tests pass. Initial compilation exposed two misleading-indentation warnings;
they were corrected before source sealing or native execution.

The ideal sequence-mixture and marginalization inequalities follow from summing
nonnegative path probabilities. They do not certify the rounded implementation
or complete package. The native experiment reports actual archives, final-coder
log costs, parent cost on prediction-time active positions, and complete added
source/executable increments. It never equates matches with saved bytes.

Declared raw populations, each with cold native initialization:

- Development: [0,250000).
- Separate validation: [347250000,347500000).
- Confirmation: [713000000,714000000).

All are retained, historically exposed fixtures. Each P/K/I/S/W arm receives a
fresh encode, independent decode and encode repeat. A fresh uninstrumented P
archive is also generated per population. Every parent probability/truth is
compared across arms; introduced-state witnesses, complete inverse emissions and
finite archives must agree on replay. This does not claim full parent-state
serialization. The selected S identity is frozen before confirmation; there is
no corpus-driven parameter search. All three populations run even on a valid
loss, as a predeclared transfer diagnostic; no automatic larger gate follows.

Success requires S to beat P after the counted package increment, and to beat I
and W, on each population. Conditional attribution remains recorded on a loss.
A failure rejects this fixed implementation, not all cross-history dependence.

Ownership: `codex-relational-20260920`, canonical job
`20260920T134229Z_f0a6290a0b`, CPU2, resident cap 9,999,998,976 bytes, logical
scratch cap 16GB, elapsed stop 7200 seconds. Native execution remains pending
until publication and fresh admission. Current host timing is diagnostic.

Relevant established machinery: [stochastic string transduction](https://arxiv.org/abs/cmp-lg/9610005),
[XMLPPM's shared arithmetic coder and causal structural contexts](https://xmlppm.sourceforge.net/paper/node6.html),
and [Bayesian sequence prediction](https://arxiv.org/abs/cs/0301014).
These support the foundations, not a claim that this particular mechanism is
new globally or achieves the corpus target.

## Implementation repair before interpretation

The first native job was interrupted after source review reproduced a parser
classification defect: `title` and `text` from closing tags entered the word
reservoirs. [The executable probe and failure record](../results/fx2_relational_binding250k_q0_v1/failure.json)
retain the exact original source, input, observed records, partial native output,
and clean process termination. The validated reflection is implementation-failure
and inconclusive, not a scientific rejection.

The [v2 retry](../operations/adaptive/experiments/fx2_relational_binding250k_q0_v2.json)
is created by the canonical implementation-retry freezer. It inherits the
hypothesis, populations, controls and predicates. The new predictor tracks XML
tag interiors and excludes them from donor collection and mention starts. A
regression checks that tag and attribute names cannot enter either reservoir.
The three v2 synthetic tests pass, including exact posterior and repeated-donor
checks. Original v1 bytes remain preserved. The runtime now explicitly visits
development, validation, then confirmation rather than depending on JSON key
order; no tuning or selection between populations is permitted.

Accounting interpretation: the diagnostic v1 build added 48,983 bytes in its
smaller source-plus-executable alternative, including observer code. That fixed
increment already exceeds the parent development payload. The inherited paid
fixture predicate is therefore stricter than testing the binding mechanism.
The terminal interpretation must separately report S-versus-P/I/W actual payload
deltas and added code; failure to amortize code on a small fixture cannot reject
cross-history dependence. No stripped-release or full-corpus saving is assumed.

## Execution handoff

Retry job `20260920T135211Z_9ec3228a93` uses the published source at `022117dcd`.
The first independently built P archive, native P inverse and P repeat have
completed on the opening250KB; the job remains active at this handoff. No S/I/W
comparison or final scientific verdict is available yet. Consult the canonical
job and guard for current state rather than treating this paragraph as liveness.
All12 native tests and144 pure tests with54 subtests pass. The new terminal
interpreter compiles and imports; it has not yet consumed a complete native run.

Once the job is terminal, from the repository root:

```bash
PYTHONPATH=projects/enwiki9/src python3 -m gamma_enwiki9.adapters.fx2_relational_terminal \
  projects/enwiki9 fx2_relational_binding250k_q0_v2 20260920T135211Z_9ec3228a93
```

This independently checks all retained artifact identities, bound raw inputs,
archive byte counts, P/K equivalence, complete inverse emissions, parent
probability/truth trajectories, introduced-state repeat witnesses and incremental
package arithmetic. It requires all51 command records. It publishes an immutable
terminal plus15 driver rows and their index; it does not grant a scientific
transition or launch a codec. Review the actual payload/control deltas, then use
`enwiki9_lab.py reflect` with the terminal and terminal-index as evidence. Only
after that reflection should `record_driver_result.py --terminal-index` append
the closed arm set. On failure, preserve the failed execution and reflect its
actual failure class instead. No automatic full-corpus promotion is authorized.

## Terminal verification review

The separately maintained terminal interpreter now requires all 51 distinct
successful command phases and matches each to its retained command record. It
checks manifest membership and exact references for the evidence it consumes,
matches the job and candidate identities, compares P/K/S introduced state, and
recomputes the frozen paid predicate from archive sizes and actual code costs.
Parent accounting resolves the authenticated binary in the original snapshot;
an unrelated change to the current checkout cannot change that baseline.
The running v2 predictor, adapter, recipe and frozen experiment remain unchanged.

The terminal retains internal expert log-cost attribution separately from finite
archive deltas: shared versus independent bindings, shared versus wrong donors,
and shared versus parent, plus the final mixture cost. Native summaries must match
their retained artifacts. Those log costs cover the same complete modeled
population; prediction-active subsets can differ between arms and are not a
matched-subset estimate. A better internal expert can still lose to the parent
and supply no archive gain. No internal saving is added to the measured archive.

Twelve synthetic terminal tests exercise successful publication, idempotent
replay despite a changed checkout parent, and rejection of incomplete or corrupt
bundles before publication. The explicit pure CI group passes 156 tests and 54
subtests, with one historical test deselected. Compilation and imports pass.
These checks validate the evidence interpreter, not the still-running native
comparison. Its terminal, reflection and driver ledger rows remain pending.
