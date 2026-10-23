# Python transfer of vocabulary-aware naming

Board item 6, exact-string goals 2a/2b. Carry the measured JS name-search
mechanism to Python; do not assume the JS gain transfers. Source execution,
vocabulary costs and readiness are independently measured in Python.

## Population and exposure

The private historical Python stage50 has 50 already-exposed development
problems with hash-bound qualified alternatives. Intersect its qualified IDs
with the current cost-decomposition-v1 explicit development allowlist, yielding
36 problems. Preserve the current partition: 27 fit and nine validation.
The other 14 Python problems' sources/cases are not opened. No final held-out 100
or protected 66 source/case is opened. Historical metadata is not an authorization
to open those sets.

Choose the shortest previously qualified alternative per permitted ID by stored
byte length, then variant name, before new dictionary or rewrite measurements.
This gives 34 canonical-compact and two inline-row-dp sources, identified in
contract.json. Qualification and parent contract hashes, source hashes,
test-file hashes and original-observation hashes are pinned. Sources retain
their Solution class and named method interface; imports and all helpers are
included in the emitted source. No free wrapper or runtime helper is added.

These are consumed development programs, not fresh evaluation. The small panel
is a mechanism transfer test, not a representative sample of 500 problems.
Pre-freeze audit reads only the 27 fit sources: all are ASCII and parse; 142
eligible names have 649 occurrences, and one program is skipped conservatively.
No fit vocabulary, rewrite candidate costs or validation sources were measured.
Ten synthetic tests pass, including two sandbox parity controls.

## Bound-name policy

Use CPython AST positions and symtable. Group eligible local names by spelling
across scopes and apply a global injective name map to their Name/argument
spans. Free, global, nonlocal and imported spellings are reserved, even when
the same spelling is local elsewhere. Module/class bindings, functions/classes,
self/cls, attributes, keyword arguments, exception and pattern-capture bindings
are reserved. All other identifier spellings and Python keywords remain
unavailable as new targets. No token/string replacement outside the AST spans.

Conservatively skip programs using eval/exec/compile, locals/globals/vars/dir,
dynamic attribute operations, explicit frame/code/closure/annotation reflection,
decorators/type parameters, or **keyword expansion. Non-ASCII text is retained
unchanged. These guards are not a proof against all Python introspection;
independent final execution checks remain mandatory.

Reuse name-search-v1's exact coordinate policy: two sweeps per rewrite call,
names ordered by decreasing occurrences then spelling; try a–z; swap when the
target is another eligible name. Only strict whole-source minimum-selection
improvements are accepted. Tie-break by source byte length then source text.
Record original and round candidates, accepted maps and rejected hashes/costs
privately. No decoder-side renaming or binding exists: concatenated literals
reconstruct the chosen rewritten source exactly.

## Matched arms

Fit a shared starting dictionary separately at 128/7-bit and 256/8-bit, beginning
with the 96 ASCII/newline fallback entries. Use the existing chosen-parse-span
refill/local search. This is a new fit-only baseline; do not import old Python
dictionaries trained on the other 14 problems.

At each width compare:

| Arm | Sources | Dictionary |
| --- | --- | --- |
| control | Fixed selected originals | Two continuation rounds from the fit baseline |
| rename | Two rewrite calls | Frozen fit baseline |
| joint | Rewrite/search/rewrite/search | Two alternating rounds |

Fit keeps original and prior rewritten variants as selectable alternatives.
Each dictionary round uses 60,000 trials, 600-second safety cap, refill shortlist 24,
96 additions, 500 swaps, 16 pair additions,eight pair removals, 150 paired moves.
All 96 fallback characters remain mandatory. Report baseline fitting separately
from additional search. Local termination is not an optimum; time-capped
comparisons are budget-limited.

Seal all three dictionaries and chosen fit sources of a width before opening
any validation source at that width. Validation receives two rewrite calls
under the sealed dictionary, no refit. Its comparison is source-plus-encoder
optimization against fixed source, not untouched-source compression. Final
qualification happens only after both widths finish all decisions.

Exclude full sources and complete entry methods/bodies from proposed entries
across every fit variant; audit selected fit+validation sources at the end.
Any violation fails readiness without repair. Entry bodies are extracted from
the Solution method matching the frozen entry. Independent canonical packet
decoding must reproduce each selected source hash. No corpus loader may read
outside the 36 explicit source paths.

## Independent qualification

Deduplicate final changed programs by ID/hash across arms. Run every pinned
Python case through the preserved stage50 harness in the current unchanged
judge sandbox. Reuse its 32-case batch boundaries. Expected values stay outside
the sandbox. Require both the unchanged return/mutation oracle and exact JSON
observation parity with pinned original outputs, including result type, argument
mutation and alias edges. The report distinguishes fresh checks from exact-source
reuse. Finite historical cases do not prove arbitrary-input equivalence.

Use four sandbox workers, 3 CPU seconds / 8 wall seconds / 512 MiB per batch and 4 MiB
output limit. No retry, candidate repair, fallback replacement or test feedback
into rewriting. A failure stays in the denominator and blocks readiness.
Original bytes reuse the existing qualification. Keep detailed stdout/stderr
and mismatch receipts privately; public results contain metadata only.

Two width-search workers, then four sandbox workers, with no phase overlap.
PYTHONHASHSEED=0; 4 GiB per-process address-space cap; 7,200-second overall ceiling.
No training, model download or accelerator use. Ten synthetic checks and
compilation/import precede launch; A's 37 judge/lane checks cover the unchanged
infrastructure. Commit/push this design/code/contract, request Claude review,
and launch after its reply or PLAN's documented 30-minute review timeout.

## Metrics, predictions and readiness

Report both splits and all six arms: coverage/qualification, total/median/p90/
p95/worst selections and actions, <=32/96 counts, single-character fraction,
dictionary/package bytes, framing/padding, paired IDs, changed programs, fresh
case checks, rewrite trials/moves, dictionary rounds/stops and wall time.
One Finish per encoded program is charged. Navigation/correction are zero;
CPython/stdlib installed footprint is unmeasured and excluded explicitly.

- P1: control continuations preserve the learned baseline's fit and validation
  totals at both widths.
- P2: rename lowers validation actions at least 1% at 256 entries.
- P3: joint uses fewer validation actions than rename at 256 entries.
- P4: all 216 selected programs encode/decode and qualify (reuse included), with
  clean whole-solution audits.
- P5: no arm meets all M1 cost indicators even on these nine validation programs.

For development readiness, require all 36 chosen programs qualify, all 9 validation
programs decode, and no whole-solution entry. Against the same-width learned
fixed-source baseline require >=5% fewer validation actions, lower median and
p90 actions, >=6 improved and <=2 worsened programs, nonincreasing single-char
fraction, and package bytes<=105%. Six/two are the rounded 60% / 25% paired criteria
for nine cases; no M1 threshold changes. Rank ready arms by validation actions,
package bytes, then arm name. Report joint-versus-rename as a separate contrast.

Readiness permits only proposing separately frozen confirmation. This panel
cannot qualify M1's 500-problem coverage target. No private source/dictionary/
sequence publication, protected opening, BITS deployment, human study, training,
claim, ledger or catalog write. Those owner gates remain intact.

Component: algorithm_solver literal research. Intent preserved; Python source
search changes, canonical codec and production authority stay unchanged.
