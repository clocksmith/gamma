# Independent class and native adapter evidence for the existing 68-problem cohort

This lane independently tests exact selected Python/JavaScript modules from the
existing second downloaded cohort. It creates no new writing batch. Selection
contains 117 unchanged original modules, nine separately authored mandatory-
constraint repairs and ten separately authored native-wrapper repairs. The new
native sources were authored by root and independently reviewed here.

Official definition and metadata snapshots bind every selected method, ordered
interface and result type. For 189, 283, 289, 324 and 344 the metadata declares
`return.type=void` and `output.paramindex=0`. Pinned official starter snapshots establish Python `Solution.method` and JavaScript
standalone named-function entries for these five mutations. Both actual entries
execute; JavaScript class methods receive a separate compatibility check. Correctness comes from the observed argument-zero state, never the
return of a functional `solve` helper. The argument vector remains the same
length and any other arguments must be unchanged. Typed effects and alias
relationships are checked. Wiggle Sort accepts every valid strict alternating
permutation with the input multiset, rather than one canonical ordering.

The official effect adapter ignores return values. A diagnostic records the
actual return kind, and new corrected modules' None/undefined promise is checked
separately. The ten original wrappers are negative controls: they must be rejected
on nontrivial mutation witnesses. Already-correct inputs may legitimately conform
when no mutation is needed; their non-void return is not used to invent an effect
failure. Counts report these degenerate conforming observations separately.

All other 63 class methods receive independent core-value checks, unchanged-on-
return argument checks and fresh mutable-return checks. The ten changed native
modules also execute their free `solve` entry through the same core-value contract,
so evidence is not inherited merely because its body bytes were preserved.
There are 161 execution units: 136 selected class interfaces, five actual official
JavaScript named entries, ten changed-module free entries and ten original native
controls (Python class methods and JavaScript named functions).

The independent root reference/case helpers are copied and hash-bound, not
candidate-as-oracle or cross-language agreement. New native witnesses cover small
rotation and zero-placement spaces, exhaustive simultaneous board transitions,
all small wiggle inputs with an independently enumerated valid witness, printable
ASCII, and legal maximum-size effects. Native complexity review finds constant
auxiliary storage for 189/283/289/344. 324 uses a sorted auxiliary copy; its optional
linear/constant-space follow-up is not claimed. The nine mandatory repairs are
reviewed and bound to their new hashes separately from their author.

Exact sources, generated adapter bytes, interfaces, helper bytes, independent
expected results, runtime, limits and batch plan are frozen before execution.
Only a source/adapter packet, observation transport and argument packet enter the
existing isolated Linux judge; expected results stay on the host. One interpreter
at a time uses the unchanged 1 GiB address limit, three CPU seconds, eight wall
seconds and bounded output. The observed initial available memory on Jupiter was
87,653,171,200 bytes. Public services are not interrupted.

Run identity and dispatch checkpoints precede execution; raw streams precede
judging. Requested slots, captured complete observations and successful complete
interpreter streams are counted separately, including killed/partial streams.
No per-call entry marker exists, so never-started and begun-but-unfinished slots
cannot be distinguished when no complete observation was captured.

Separate replay reconstructs expectations and checks all raw bindings. Finite
source-exposed evidence is not formal proof, held-out performance, actual
production-service admission or automatic catalogue promotion. The five JavaScript aliases in this v2 source selection forward to the corrected
in-place class methods. The superseded class-only preparation remains archived and
unexecuted; no result is inherited from that earlier source selection.
