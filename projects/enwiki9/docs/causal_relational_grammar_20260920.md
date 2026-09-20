# Causal relational grammar: first native binding comparison

The user-selected research direction is persistent relational argument binding
across structure and content histories, with one existing FX2 coding sequence.
The target remains 96,000,000 complete bytes, 95,000,000 stretch; verified full
corpus score is unknown. The earlier split and retraining losses remain intact.

## Closed result: fixed realization parked

The unchanged v2 comparison completed all 51 phases on 2026-09-20. The
[independent terminal](../results/fx2_relational_binding250k_q0_v2/terminal.json)
verified 661 retained artifacts. The validated
[reflection](../operations/adaptive/reflections/20260920T135211Z_9ec3228a93.json)
records a valid negative result and holds this realization. All 15 arm rows are
recorded through the [terminal index](../results/fx2_relational_binding250k_q0_v2/terminal-index.json);
the recorder's check reports zero missing rows. No successor is selected.

| Raw population | P / K archive bytes | I / S / W archive bytes | S minus P |
| --- | ---: | ---: | ---: |
| Development 250KB | 33,429 | 33,433 | +4 |
| Separate validation 250KB | 35,464 | 35,469 | +5 |
| Confirmation 1MB | 131,238 | 131,257 | +19 |

The following are native floating log-cost differences on each complete modeled
population. Positive values in the first two columns favor shared bindings;
positive values in the last two columns are losses against FX2. These are not
archive bytes and do not compare differently selected active subsets.

| Population | I minus S expert bits | W minus S expert bits | S expert minus P bits | Final mixture minus P bits |
| --- | ---: | ---: | ---: | ---: |
| Development | +3,891.790 | +68.245 | +32,929.145 | +35.998 |
| Validation | +4,506.705 | +97.011 | +36,617.350 | +38.995 |
| Confirmation | -3,586.827 | -278.254 | +189,629.966 | +156.016 |

Persistent identity helps this expert on the two 250KB populations, but that
advantage reverses on 1MB, including against the wrong-donor control. The expert
loses substantially to FX2 on all three populations. The final mixture protects
the parent from most of that loss; it does not hide a demonstrated net advantage
of the expert over FX2. Equal I/S/W archive sizes do not mean equal internal
predictions or identical archives.

The populations span 37, 40 and 160 declared mixture epochs, respectively. Small
mixture losses alongside a much larger expert deficit are consistent with
fallback protection and repeated restarts. Aggregate measurements do not isolate
reset policy from Q48/Q16 effects, and no epoch-level or numerical intervention
was run. The finite archive differences are 32, 40 and 152 bits; subtracting the
native mixture log-cost differences leaves -3.998, +1.005 and -4.016 bits. This
observed finite-coder length difference is not a bound on posterior rounding or
a reason to change resets. The expert's lack of competitive value is already
visible before that issue.

The [package record](../results/fx2_relational_binding250k_q0_v2/package.json)
counts a 49,038-byte implementation increment in the smaller alternative:
8,056 added source-ZIP bytes, 40,960 added decoder-executable bytes and 22 option
bytes. The alternative with two executables adds 81,942 bytes. The model,
dictionary and frontend are unchanged. Observer code is conservatively included;
no stripped-release reduction is claimed. A delivery counts its fixed increment
once, not once per research sample, and the alternative representations are not
added together. Every measured sample already loses before this increment.

All independent inverses, deterministic archive repeats, original-parent
probability/truth comparisons and P/K/S introduced-state checks pass. The bound
diagnostic job on one logical CPU (CPU2) completed in 3,694.923 seconds, peaked at
6,462,992,384 cgroup bytes, 470,904,832 allocated scratch bytes and
15,133,469,865 logical scratch bytes, and finished with every guard flag false
and cleanup complete. The [guard](../run_logs/adaptive/20260920T135211Z_9ec3228a93.resources/guard.json)
provides diagnostic resource evidence, not independent prize qualification.

Park this four-donor, exact-spelling, 4,096-modeled-byte-epoch realization. Preserve
the broader cross-history hypothesis and all original artifacts. No new mechanism,
reset change, training run or larger gate follows. A successor requires a specific
unresolved cause grounded in the terminal attribution. The complete full-corpus
score remains unknown and the objective receives zero score credit.

## Frozen implementation and original design

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
scratch cap 16GB, elapsed stop 7200 seconds. This original attempt was interrupted
as described below; the separately owned retry is now closed. Timing is diagnostic.

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

## Closed execution and replay

Retry job `20260920T135211Z_9ec3228a93` used published source `022117dcd` and
completed unchanged. The terminal and canonical reflection now bind its final
result. To rerun the independently maintained terminal verification from the
repository root:

```bash
PYTHONPATH=projects/enwiki9/src python3 -m gamma_enwiki9.adapters.fx2_relational_terminal \
  projects/enwiki9 fx2_relational_binding250k_q0_v2 20260920T135211Z_9ec3228a93
```

Identical publication is idempotent. The terminal checks retained artifacts,
bound raw inputs, original P/K archives, complete inverse emissions, parent
probability/truth trajectories, introduced-state witnesses and incremental
package arithmetic. Reflection precedes the closed arm-set ledger append.
All fifteen rows are recorded; no additional launch is needed to close this run.

## Terminal verification review

The separately maintained terminal interpreter now requires all 51 distinct
successful command phases and matches each to its retained command record. It
checks manifest membership and exact references for the evidence it consumes,
matches the job and candidate identities, compares P/K/S introduced state, and
recomputes the frozen paid predicate from archive sizes and actual code costs.
Parent accounting resolves the authenticated binary in the original snapshot;
an unrelated change to the current checkout cannot change that baseline.
The measured v2 predictor, adapter, recipe and frozen experiment remain unchanged.

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
These synthetic checks validate the evidence interpreter; the separate complete
native comparison supplies the scientific result above.

## Integrated synthetic binding checks

The [integration fixture](../tests/causal_relational_integration_fixture.cpp)
passes both title-to-content and content-to-link sequences through the complete
sealed v2 WRT inverse, field parser, donor reservoirs, binding updates and outer
mixture. Four distinct completed words precede the declared epoch boundary;
180 subsequent mentions reuse one donor. The parent is an explicitly uniform
bit predictor. This constructed source is separate from the corpus populations.

In both directions, S has lower returned-probability log cost than P, I and W.
P and K preserve every parent probability; P/K/S introduced state agrees at each
modeled-byte boundary. Every arm reconstructs the exact input and stays within
the existing synthetic state bound. Undefined-behavior sanitization passes.
The fixture makes no finite-archive or complete-package claim. It closes the
integration gap between the earlier isolated Binding-kernel gain and a complete
Model path; it does not establish improvement over competitive FX2 predictions.
No sealed candidate source or parameter changed for this check. The explicit
native CI group passes all 13 tests, including this integration fixture.
