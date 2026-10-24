# Item46 prelaunch freeze draft: fixed-dictionary spelling transfer

2026-10-23 EDT. **Publicly bound, inactive, not execution-frozen.** Neither private
input nor cases have been opened for implementation. Both item43 arms now have
complete independently replayed records at `ded5c3fef`. An inactive pending
contract binds those records, actual item24, and the corrected item13/24/43 source
lineage. Item41 supplies only optional exact-ID/hash qualification reuse; its D10
base differs from these sources. Public-only independent reconstruction verifies
484 known ID/hash receipts and ten matched standing-reference policy views.

Root reviews the implementation and synthetic checks; Claude reviews the final
pushed freeze; only then may exact pending-to-active activation authorize a run.
No missing or failed parent may be dropped. This document implements the original
six-view design in [DRAFT.md](DRAFT.md); that draft's design-only status describes
its earlier stage, not an authority to run this implementation.

## Population, dictionaries, rules and decisions

Mandatory pairs are actual item24 optional U/S, item43 nonregress U/S, and item43
unweighted U/S. U keeps original sources. S applies the known item41 spelling
rule to the corresponding fixed dictionary. All use the same original300fit and
100consumed-validation hashes, proven against public item24/43 qualification
chains. Protected66 and final-heldout100 remain closed. This is a transfer and
stacking test on consumed development, not a novel component or independent
confirmation. Item41's failed atomic J verdict and all its gates stay unchanged.

Preserve actual parent dictionary bytes and order, including its paid characters;
<=256 entries, eight-bit IDs, no fallback or restored characters. `common.evaluate`
is the fixed-order adapter: item41 `core.evaluate` silently sorts and is not used.
Use exact min(N,C,complete IDs) for decisions; measure canonical min(N,complete IDs)
as a mandatory complete shadow. No policy is chosen on outcomes. N excludesFinish;
actions=N+1. Character fraction uses C/N, never actions in its denominator.

For each anchor derive exactly one menu from original fit sources with its fixed
dictionary and the unchanged item41 rule: first four item27 palette names plus
aa..ah, deduplicated; top16 normalized windows of2–6 selected pieces, <=160bytes,
complete occurrences of one legal binding, >=2fit owners, exact frozen ranking.
Seal that menu before local fit application. No aggregate item41 fit-group search,
new menu round, context refit, dictionary proposal or atomic admission runs.

Apply the identical sealed menu locally to fit, then to validation after all-fit
seals. Numeric source-ID order, at most two passes per source, <=192context/target
opportunities per pass. One deterministic eligible binding per transaction;
rename its complete declaration/reference spans with inherited capture/unsafe
and non-ASCII/UTF-16 guards. Keep every offered variant, including ineligible or
uncovered variants. Score covered proposals exactly. Admit only a strict local
lex(N,C,raw package) improvement, choose best by inherited deterministic tie rule,
and keep original on exact ties. At most153600rendered proposals per anchor across
all400sources. Initial unencodable sources remain failures; spelling cannot rescue
them. A non-ASCII source is never renamed; inherited ASCII representation/parser
failures remain failures, not a new Unicode support claim.

All six views share the union of source/body bans from originals and every
encountered variant in every arm, including rejected variants. Each worker checks
new bans against every fixed dictionary. The coordinator merges every retained
ledger and rechecks all dictionaries before all-fit and all-validation barriers.
Any cross-arm collision stops overall eligibility before cases. No pruning,
variant deletion, silent fallback, arm substitution or budget retry is allowed.

## Exposure, qualification and replay

Fit-only source files are hash-checked first. No combined validation source carrier
is hashed/read before all three fit source/menu/dictionary/trace/ban seals and the
shared legal fit-union receipt. Item43 private result metadata containing validation
is also deferred. Each validation worker uses the already sealed menu and fixed
dictionary; no aggregate validation outcome changes any choice procedure.

All final fit/validation choices and the complete global ban union are sealed
before cases or baseline observations. Reuse qualification only from exact passing
ID/source-hash receipts bound through item24, both43 and41 independent evidence.
Every previously unqualified selected hash runs all pinned strict checks exactly
once across arms, with inherited sandbox limits and full raw output/exit/timeout/
output-limit receipts. No qualification-guided fallback. Source failures remain
in all denominators. Expected observations stay outside the sandbox.

The independent reporter reconstructs initial/menu identities, every local offered
proposal, lex costs/ties and accepted transitions, all global bans and seals,
full ordered dictionary packets under both policies, qualification reuse and raw
strict-observation rejudging. It executes no candidate and runs no optimizer.
Original/selected source hashes, all input/implementation/runtime pins, complete
mandatory arm sets, budget/timing receipts and failed cohorts are checked. Unknown
public fields or source-containing payloads are not copied through publication.

## Gates and predictions

All gates are checked under both policies. Full400 coverage/qualification/legality
is a prerequisite. The paired transfer hypothesis is on consumed-validation100:
S has nonincreasing actions, median, p90 and package versus its own U, and strictly
lower C/N. Fit improvements are separate diagnostics, with no strict fit-fraction
gate. A primary-only effect is recorded separately and cannot pass both policies.

An eligible successor additionally passes original R readiness: >=5%fewer actions,
strictly lower median/p90, >=60better and <=25worse IDs, nonincreasing C/N and raw
package<=105%. It passes strict action/nonworse median,p90,fraction,<=25worse and
package<=105% against seed13, actual24, N and NCP, using their same-policy qualified
item30 reference rows. It must also pass those strict incremental predicates versus
record-time current best. A separately supplied, hash-bound record-time best
receipt selects the comparator, not the candidate. If that receipt or its exact
policy comparison is unavailable, replacement is unresolved; do not default to24.
For a named24/43parent, its freshly independently replayed U view supplies both
policies. Other current-best evidence must be separately source-bound and qualified.

All three S candidates are eligible in advance; rank passing candidates by
canonical actions, canonical full package, fixed arm label, with both-policy gates
required. A fraction-only change versus own U can establish transfer, but equal
actions versus the actual current best cannot replace that best. No change to
M1's400/500,<=256,median<=32,p95<=96,<=10%C and zero-whole-body gates, no default
promotion, and no change to item13's separately frozen confirmation subject.

Predictions: P1all mandatory views cover/decode/qualify (true); P2at least one S
lowers validationC/N at unchanged actions under both policies (true, uncertain
transfer); P3at least one43-S passes paired transfer (true, dictionary-dependent);
P4no S replaces record-time current best (true). Incomplete runs give no numerical
verdict; missing current-best binding makes P4unknown, not true by default.

## Budgets, output and failure dominance

Three spelling workers use cores0/1/2, one thread each, <=8GiB address space. A
single1800-second absolute per-anchor deadline starts before fit loading; it covers
menu construction, fit application/finalization, barrier waiting, validation and
both U/S packet measurements. Starting a validation worker never resets it. The
153600proposal cap includes uncovered offered variants; initial encodings and
menu analysis are measured setup within the same deadline. Exhaustion is an
incomplete arm, never successful truncation. Store all partial receipts.

Production supervisor and runner use0–3, <=8GiB, a3600-second whole cap including
all preflight, preparation, choices, four disjoint-core qualification queues and
output. Qualification retains the inherited900-second per-source hard guard.
Independent replay has a separate1800-second whole cap, same cores and memory.
Normal Python assertions are required; OMP/OPENBLAS/MKL threads1. Both outer
phases launch a fresh process group and kill/reap it on exit/failure under a
separate10-second cleanup tolerance. Timeout classes cannot be swallowed by
ordinary exception handling. Remaining cleanup time is checked before blocking
operations. Success publication follows cleanup/log close and remains inside the
original phase deadline. Failed receipt writes cannot bypass independent removal
or incomplete replacement of success artifacts. No restart or budget enlargement.

Private artifacts retain menus, full sources, all variants, packets, traces,
qualification output and status. Public output is allowlisted metadata/hashes:
both split totals and paired counts, C/N,N,actions,median/p90/p95,source-byte and
spelling-length changes, dictionary/header/payload/padding, raw/full package,
decoder bytes, offline implementation bytes, measured time/memory. Charge the
whole dictionary once per reported cohort. Models/training zero; installed runtime
size unmeasured. Partial coverage is explicitly partial and cannot pass a gate.

## Pending commands, unavailable until reviewed binding

The binder is public-only and refuses absent/incomplete43records. Do not invoke it
before root permits the stage boundary. Once implementation and both parents are
reviewed, it writes inactive pending-contract.json. Activation rebuilds exact
pending equality and changes only active=false totrue. Runtime rejects unbound or
inactive contracts before private hashes/loads. The root then pushes activation.

After that separate authorization, production uses `supervise.py --phase production
--output <new-private-run>`; replay uses `supervise.py --phase report --run
<completed-private-run> --output <new-report-directory> --record-time-best
<reviewed-metadata-binding>`. These examples grant no execution authority.
