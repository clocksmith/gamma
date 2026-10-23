# Item41 execution freeze: atomic naming and paid literal entries

Prelaunch draft. Requires root review, pushed immutable commit and Claude cross-review.
No private source, test, baseline-observation or corpus performance input has been
opened to prepare this implementation. Contract preparation uses only existing
public metadata and opaque inherited input hashes. This document grants no launch. The binder writes pending-contract.json with
active=false. After review, --activate must rebuild an exactly identical pending
contract before flipping only active to true; any drift is rejected. Runner, worker
input boundary, qualifier and supervisor reject inactive contracts before private
input hashing/loading. Root activates and pushes the immutable active freeze.

The detailed scientific design and disclosed adaptive basis are in [DRAFT.md](DRAFT.md).
Item30 D10 is fixed before probes:256 entries,92 actual character entries; all400
D10/D11 per-ID public source hashes and300/100 partitions agree. The six existing
item32 source-carrier file hashes are inherited; those D11 files supply byte-identical
**source bytes only**, while the dictionary is actual D10 with its separately pinned
JSON/binary hashes. No D11 dictionary is selected. All closed final100/protected66
sources and cases remain closed. No new cases, production changes or M1 relaxation.

## Fixed search and decisions

D/S/A/J and untouched D10 are mandatory. D changes dictionary only; S changes safe
binding spellings only; A admits those separately; J adds atomic source+paid-entry
transactions. Every searched arm uses exact min(N,C,complete IDs) segmentation and
strict lex(N,C,raw package) admission. Canonical policy is a complete shadow, never
an alternative selected after results. Item18 already used lex plateaus; the new
hypothesis is atomic source/dictionary admission, not lex ordering.

Names: first four from the frozen item27 palette rule plus eight fixed names
`aa,ab,ac,ad,ae,af,ag,ah`, deduplicated. Contexts: top16 normalized windows of2–6
selected pieces and at most160 bytes, with complete occurrences of one eligible
binding, support at least2 IDs, ranking fixed in DRAFT. Groups: at most one legal
binding per program, all of its declaration/reference spans; at most192 groups.
No non-ASCII source is renamed: inherited Acorn UTF-16 versus Python offset safety
retention applies at both fit and validation boundaries. Unsafe/capture guards are
unchanged. An arbitrary identifier substring or literal string occurrence is never
renamed.

Paid entries: target alone or target plus rendered context, at most384 possibilities.
Ordinary dictionary control: top24 selected-piece merges plus first8 adjacent pairs.
Protect exactly initial92 character entries. Probe all other single deletions,
rank top12 by full lex loss, enumerate at most12 ranked removal combinations for
capacity256. Every complete state evaluation, deletion probe and coverage failure
counts toward the same10,000 trial cap. Same round-robin proposal procedure and
caps, not identical opportunities after trajectories diverge. A comparison has no
posthoc reduced comparator set.

All encountered source/body bans, including rejected/ineligible rendered variants,
remain. If a new ban makes the incumbent dictionary illegal, preserve the variant,
trace and incumbent; stop with legality failure and no matched verdict. Do not
remove an entry, undo the ban, substitute an arm or rescue an uncovered source.
Per-menu rendered-group IDs include ineligible groups and partial prefixes.

Four single-core workers use0/1/2/3. Each has8GiB RLIMIT_AS applied before fit input
loading,600-second between-work soft budget including menu/deletion probes and
finalization in measured elapsed,10,000 counted full evaluations, and a900-second
hard signal deadline covering setup, parser calls, in-flight trial and finalization.
A trial/finalization may overrun600; report actual elapsed and overrun. The parent
also has8GiB before input preflight. The supervisor binds0–3, OMP/BLAS1, normal
Python assertions (reject -O/PYTHONOPTIMIZE), and kills the full runner process
group after3,600 seconds or termination, preserving status/failure receipts and
partial artifacts. The same four cores are reused by at most four qualification
workers, each with the same memory and900-second per-source hard guard. No retries.
Root schedules execution only when its core allocation is free.

## Exposure, qualification and independent replay

Verify public runtime/code pins and fit-carrier files first. The combined source
carrier containing validation is neither content-hashed nor loaded until all four
fit-seals exist. Each seal binds fit sources, dictionary, name list, context list,
full trace, menus and accumulated bans. Names must agree across all arms.
Validation applies only the sealed name/context rule and fixed dictionary, at most
two passes per source. Local exact cost choice uses consumed validation inputs;
this is disclosed development adaptation, not independent confirmation. No aggregate
validation choice changes fit names, contexts, sources or dictionaries.

Seal every final validation source choice before hashing/opening case contents or
baseline observations. Reuse only exact(ID,source hash) passing receipts from pinned
public item30 evidence. Every new selected hash executes all pinned cases once with
unchanged strict return/observation parity and sandbox limits. Keep raw sandbox
stdout/stderr, offset/count, input/harness/source digests, command/limits and
exit/signal/timeout/output-limit metadata for every batch, including failure.
Independent reporting must rejudge those observations without executing candidates.
The report has its own900-second hard signal guard,8GiB and cores0–3; a report
timeout writes a no-verdict failure receipt and does not launch experiments.
Unqualified, uncovered or timed-out sources stay in every denominator; a failure
cannot be replaced by a parent hash.

The separate report reconstructs both exact policy packet sequences, decoder output,
N/C/actions, all quantiles and charges (partial covered-only quantiles are explicitly
labeled and never satisfy full-coverage gates), source hashes, body bans, geometry and every
accepted fit/validation transition. Check source spelling length distributions,
source-byte deltas and introduced names. Dictionary/header/payload/padding and
per-program raw plus decoder-inclusive cost are charged;13,010 decoder bytes are
required from exactly literals.py and pass2/working/bitpack.py. Offline tool source
bytes are reported separately; model bytes/training steps are zero. Complete failure
receipts block any readiness verdict; reporting failures get an explicit no-verdict
receipt rather than only an assertion traceback.

Preserve R readiness: all400 covered/qualified, clean <=256 dictionaries, at least60
validation improvements and at most25 regressions, at least5% fewer actions,
strictly lower median/p90, nonincreasing C/N fraction, raw package <=105% of R.
Preserve strict incremental actions/nonworse median,p90,C/N, <=25 regressions and
package <=105% against seed13,best24,N,NCP. Additionally require the same incremental
checks for J versus D10,D,S,A; every comparison arm must qualify. Only J is eligible;
C-only gains and alternative-arm wins cannot pass the strict-action checks. M1 stays
400/500 admitted,<=256 entries,median<=32,p95<=96,<=10%C,zero whole-body entries.
Consumed-development success does not authorize default promotion or confirmation.

Predictions disclosed after27/18/30: P1 all final views decode and qualify;
P2 J accepts at least one atomic source+entry transaction on fit; P3 J validation
actions are fewer than A; P4 J fails at least one successor gate. Evaluate separately.
Conditional attribution marks untested singleton/companion subsets unknown and
records differing removals; no atomic admission alone proves a universal barrier
or that every paid entry was necessary.

## Commands after reviewed freeze

```sh
/home/x/deco/gamma/.venv_rocm/bin/python -B projects/algorithm_solver/literals/atomic-naming-entry-v1/launch.py --source-run /home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/stacking/run-v1 --output /home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/atomic-naming-entry/run-v1
```

Output directory must be new; a refused repeat launch cannot overwrite its failure
metadata. After successful execution, root runs:

```sh
/home/x/deco/gamma/.venv_rocm/bin/python -B projects/algorithm_solver/literals/atomic-naming-entry-v1/report.py --run /home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/atomic-naming-entry/run-v1
```

Root runs the independent report after completion,
retains all failed predicates and receipts, then records evidence under team policy.
This prelaunch draft and contract are finalized only after runner/report focused
synthetic checks and cross-review; do not change frozen files after launch.
