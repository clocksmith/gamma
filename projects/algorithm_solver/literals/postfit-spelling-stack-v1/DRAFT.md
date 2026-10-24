# Item 46: post-fit spelling with fixed dictionaries

2026-10-23 EDT. Design only. No private source, dictionary, case or result artifact
was opened for this draft. No implementation, binder, freeze or run is authorized
by this file. Finish item 43's independent record, prepare synthetic checks, then
freeze exact identities, budgets, predictions and controls for root/Claude review.

## Question and existing evidence

Can the spelling mechanism measured in [item 41](../atomic-naming-entry-v1/README.md)
reduce character selections under the actual item 24 dictionary and both dictionaries
from [item 43](../nonregress24-v1/FREEZE.md), while preserving their action gains?
This is a flat-literal 2b development comparison. It changes source spelling under
an already fitted dictionary; it performs no further dictionary optimization.

Item 41 measured a real D10-specific effect: S/A/J each changed 21 validation
sources, replacing 82 one-byte binding occurrences with six-byte names. Actions
stayed 8,324; primary character count fell 4,047 to 3,965 and fraction 49.2096% to
48.2125%. Canonical character count fell 4,109 to 4,027 and fraction 49.9635% to
48.9664%. Source bytes rose by 410. All fit arms accepted zero moves; no atomic
transaction benefit was demonstrated. J failed its frozen strict-action comparisons
against D10/D/S/A. Those failures and rules remain unchanged.

Those observations do not show that the names are useful or representable under
item 24 or item 43, whose dictionaries differ. Item 43's pending fit progress is
not an accepted action gain. The new test must wait for both sealed arm artifacts
and their independently replayed public record. Rechecking old item 41 packets
would verify implementation only, not supply another independent observation.

## Fixed candidate inventory and paired controls

| Fixed parent | Untreated view | Spelling view | Purpose |
| --- | --- | --- | --- |
| Item 24 actual optional dictionary | 24-U | 24-S | Test transfer from D10 to the established dictionary |
| Item 43 nonregress final dictionary | 43N-U | 43N-S | Combine the breadth-constrained dictionary with spelling |
| Item 43 unweighted final dictionary | 43W-U | 43W-S | Same spelling procedure on the matched uncapped dictionary |

All six views are mandatory, with both 43 arms named before their validation
outcomes are known. Bind each dictionary's exact bytes, order, parent seal and
public independent-evidence digest. All three parents use item 24/item 13
scope_joint256 source identity; prove all 400 per-ID hashes and partitions match,
rather than relying on that historical assertion. If an identity differs, stop
binding and revise a new draft before any run. Never select only whichever 43
arm looks best on validation. Both 43 arms must be complete and independently replayed before binding; a partial
or missing arm blocks the whole experiment, rather than reducing this inventory.
Parent failure is retained; no substitution with another dictionary. A parent's failure of readiness alone is not exclusion if its
sealed output is complete, legal, covered and independently replayed: the paired
spelling experiment may test whether its fraction weakness changes.

U always retains the parent's original source bytes. S starts from exactly those
bytes. Each pair shares one unchanged dictionary and identical encoder/decoder
policies, charges, input population and qualification requirements. Item 41's
`core.evaluate` sorts vocabulary internally, so it cannot be reused blindly for
these imported dictionaries. Preserve each parent's bound order with a small
fixed-order scoring adapter around its unchanged segmentation routine; verify
exact parity with item 41 when the supplied order already agrees, and add a
non-sorted dictionary fixture demonstrating complete-ID ties remain parent-bound.
Never sort a parent to make the compatibility check pass. No entry is
added, deleted, reordered to improve a tie, or implicitly restored; in particular,
do not restore item 24's four freed characters. Actual cardinality and all paid
character entries must be verified, never inferred as 96.

No additional D10 execution arm is proposed. Its recorded U/S views remain
labeled historical diagnostics; replay is not another independent observation.

## The inherited menu rule and bounded spelling procedure

Reuse item 41's frozen `core.names`, `core.contexts`, `validation_matches`,
`make_group`, legality/render authority and exact segmentation semantics unchanged.
This means the **same rule**, not transplanting the successful validation bindings
or selecting item 41's observed six-byte spellings by hand. Menus are derived once
from each anchor's original 300 fit sources and its fixed dictionary. Thus different
dictionaries may expose different menus; paired U/S comparisons isolate the full
fixed-rule spelling component, not a common-menu dictionary interaction.

1. Parse fit bindings with the inherited unsafe/capture exclusions. Derive the
   item 27 palette using its exact existing rank/exclusions and arguments 40/12;
   take the first four names, append `aa,ab,ac,ad,ae,af,ag,ah`, and deduplicate in
   order. At most 12 targets. No name is chosen using validation or its outcome.
2. Encode original fit sources with exact minimum `(N,C,complete ID sequence)`.
   Enumerate windows of 2–6 selected pieces, at most 160 bytes, containing complete
   occurrences of one eligible binding without cutting an occurrence. Normalize
   those spans as placeholders. Require at least two distinct fit owners; rank by
   owner count descending, summed `(window pieces - 1)` descending, then the exact
   canonical normalized tuple. Keep the first 16 contexts, using item 41's code.
3. Seal these names and contexts before local spelling. Apply the sealed menu to
   fit sources, independently per source, in fixed numeric-ID order. This local
   fit application is new relative to item 41's aggregate fit-group search; it
   deliberately uses item 41's validation application rule on both splits. Do
   not run that aggregate fit search, refresh contexts after a rename, or invoke
   item 41's dictionary/atomic proposal engine.
4. For each source perform at most two passes. Reparse the current source; match
   sealed contexts; for each context/target use the inherited deterministic legal
   binding choice (most occurrences, then binding ID). Rename all declarations
   and references of that one binding. No arbitrary substring or literal-string
   replacement. Non-ASCII/unsafe sources retain original bytes; UTF-16/span safety
   and capture guards stay unchanged.
5. Exactly score every offered variant with the fixed paid dictionary. Reject
   uncovered proposals. Accept at most one best strict lexicographic improvement
   `(N,C,raw package)` per pass, with item 41's complete deterministic tie rule.
   If no strict improvement exists, stop that source. Retain unchanged source on
   an exact tie. This gives at most 384 rendered opportunities per source and
   153,600 across its 400 sources per anchor, before early stops/empty menus.

N counts selections excluding Finish; actions are N+1 per source. Package includes
dictionary and packet framing/payload; the fixed decoder adds the same constant.
Source-length tie breaking cannot admit a cost tie. Lower lexicographic `(N,C)`
does not guarantee lower C/N when N drops, and primary character improvements do
not guarantee canonical character improvements. Both actual fractions remain gates.

Preserve every encountered source/body ban, including rejected, uncovered and
ineligible rendered variants, with the same encounter ordering as item 41. Audit
the entire unchanged dictionary against the cumulative bans. A new ban colliding
with that dictionary is a retained legality failure, not grounds to prune the
entry, remove the variant or revert the ban. The named representation population includes all six views: take the global
union of original sources and all newly encountered fit/validation variants from
all three spelling arms, including rejected variants. Every dictionary is checked
against that same global union, not merely its own arm ledger. After each new ban
batch, a collision with any one of the three dictionaries is an overall retained
legality failure with no eligible candidate or rescue. Any available complete U
metrics may remain explicitly descriptive. Reconcile all arm ledgers into the
global union before every fit/validation barrier and in independent replay.
Parallel workers may retain local ledgers, but the coordinator must merge and
check them before any global selected-choice seal or qualification. A collision
invalidates the whole experiment even if other workers already finished locally;
retain every ledger and never publish their local completion as overall acceptance.

## Exposure, coverage and qualification order

Use the same 300 fit / 100 consumed-validation IDs. Fit source carriers must be
separate: neither read nor content-hash combined validation carriers until all
three fit runs have sealed original identities, dictionaries, names, contexts,
selected fit hashes, traces, offered variants and cumulative bans. Bind an all-fit
barrier. No validation observation may regenerate a fit menu or dictionary.

Then U measures unchanged validation sources. S applies its already sealed rule
with the fixed dictionary, independently per source, using the same two-pass
procedure. First verify original coverage and legality: an uncovered starting
source remains a failure and cannot be rescued by spelling. No aggregate validation
selection of a name, context, policy, arm or budget is permitted. This local cost
selection uses consumed validation inputs and is explicitly development adaptation.

Seal all three arms' final fit and validation source choices before any case or
baseline-observation contents are opened or hashed. Reuse qualification only by
exact `(problem ID, source SHA-256)` from pinned passing receipts, including the
item 24 and both item 43 qualification records (with their inherited receipt
chains verified), and item 41's exact-hash receipts where they match.
A new hash requires every pinned strict behavioral/effect check, once per distinct
ID/hash across arms, with no qualification-guided alternative choice. Retain raw
sandbox observations, expected data outside the sandbox, harness/input/runtime
hashes, output limits, exit/signal/timeout status and failure receipts. Any selected
source failure remains in its full denominator; no source fallback or retry.

Independent reporting reconstructs both policies and every offered local proposal,
rechecks binding geometry/capture safety, complete encounter bans, menu derivation,
seals and strict admission, and decodes all selected packets to exact source hashes.
It independently rejudges fresh qualification observations without candidate
execution. Reused receipts remain reused, not new strict executions. Shared source
hashes across arms count once for fresh qualification. No partial cohort metric
is labeled full-cohort or allowed to satisfy a gate.

## Attribution and unchanged successor standards

Report both primary min(N,C,complete IDs) and canonical min(N,complete IDs) for
all six views; neither policy is chosen after results. Re-encode every baseline
under the matching policy. Historical canonical numbers cannot substitute for a
missing primary-policy comparator. Such a gap blocks that verdict until a
separately authorized, source-bound replay supplies it; no comparator omission.

A **spelling transfer benefit** is a descriptive paired result: complete/qualified
and legal U/S over all 400 programs, then on the consumed validation 100 no
increase in total actions, median/p90 or package, and strictly lower C/N under each
policy. Fit cost and fraction changes are separate diagnostics, not an additional
strict-fit-fraction gate. Strict actions versus the own U control are not
required for this hypothesis. Report separate pass/fail predicates and actual
signed changes, including a primary-only effect if canonical predicates fail.
At fixed action count, distinguish fewer character selections from source-byte
reduction; the item 41 mechanism increased source bytes. Do not call either effect
an atomic dictionary transaction or a stronger semantic abstraction.

A **successor/current-best candidate** must independently satisfy all of these:

- Complete coverage and qualification for all 400, clean <=256 dictionary,
  independently decoded packets, no run/replay failure, and passing matched
  spelling-transfer checks above.
- Original R readiness: at least 5% fewer validation actions, strictly lower
  median and p90, at least 60 better and at most 25 worse programs, nonincreasing
  C/N, and raw package at most 105% of R.
- Standing incremental comparisons against item 13, actual item 24, N and NCP:
  strictly fewer validation actions, nonworse median/p90 and C/N, at most 25 worse
  programs, and package at most 105%, matching item 41's standing comparators.
- The same strict incremental predicates against the current best recorded at
  this run's record time, under both policies. Freeze that concurrency rule before
  the experiment, as item 41 did; a missing exact-policy comparator means no
  current-best replacement is established.

All three S candidates are predeclared eligible; report every one's full table.
Rank any passing candidates by canonical actions, canonical full package, then
fixed arm label, with all primary-policy gates also required. This is an explicit
new comparison, not substitution into item 41's failed J verdict. A spelling arm
can demonstrate fraction transfer at unchanged actions without being a successor.
In particular, if 43N becomes current best and 43N-S only lowers its fraction at
identical actions, 43N-S fails strict actions against that best. Stacking does not
waive this requirement; action gains must come from the candidate relative to the
actual current best, not from a historical comparator alone.

M1 remains its original 400/500 admission, <=256 entries, median <=32 and p95 <=96
selections, <=10% character fraction and zero whole-body entries. Report its gaps
separately. Development readiness grants no default deployment or protected
confirmation. Item 13's frozen confirmation subject is unchanged.

## Charges, predictions and implementation prerequisites

Report fit and consumed-validation totals and paired per-ID counts: N, actions,
C, C/N, median/p90/p95 selections and actions, source-byte delta, changed bindings
and occurrences, spelling-length distributions, dictionary/header/payload/padding,
raw and decoder-inclusive package, and exact decoder dependency bytes. Charge the
whole fixed dictionary once per reported cohort. Record all proposal/parsing,
qualification and replay time and peak memory; include offline implementation
storage, zero model/training costs, and disclose unmeasured installed runtime size.
Public output contains metadata/hashes only, never sources, dictionary strings,
name/context literals, cases or raw sandbox output.

Proposed falsifiable predictions, to freeze before execution: P1 all mandatory
views cover, decode and qualify (expected true); P2 at least one S reduces C/N
versus its U at unchanged actions under both policies (expected true, transfer
uncertain); P3 at least one 43-S passes the spelling-transfer check (expected true,
dictionary-dependent); P4 no S replaces record-time current best (expected true).
Evaluate failures as failures, with no numerical verdict from an incomplete run.

Before implementation, review the new local-fit application and per-anchor menu
choice explicitly. Required synthetic checks: exact menu parity with item 41;
complete-ID policy ties; useful spelling at unchanged N; covered and uncovered
proposals with optional characters; no rescue of an uncovered starting source;
unsafe/capture/non-ASCII retention; rejected-variant ban invalidation; exactly two
passes; fit/validation/case barriers; qualification reuse versus fresh hashes;
corrupt packet/seal rejection; cleanup/deadline/receipt failure dominance.

Tentative resource envelope for that future freeze: three single-core spelling
workers on 0/1/2, <=8 GiB each, max 153,600 counted per-source proposal evaluations
per anchor, no repeated menu fitting, and a 1,800-second absolute per-anchor deadline from fit start, including fit
finalization and the shared fit-barrier wait before validation. No new worker
replenishes that deadline. U
measurement runs within the same arm budget. A supervisor on 0–3 bounds the whole
production including qualification to 3,600 seconds, at most four strict sandbox
workers with inherited per-source limits, plus 10-second bounded group cleanup.
Independent replay receives a separate 1,800-second cap and <=8 GiB. These are
proposed ceilings, not runtime forecasts or launch authority; synthetic mechanism
checks must justify them before freeze. Cap interruption is a retained incomplete
arm, not a successful truncated sweep. No retries or alternate parent selection.

The scientific merit is transfer and matched stacking of a known component, not
a novelty claim. Component intent is preserved: qualified flat-literal representation evidence,
complete costs, retained failures, and separate consumed development versus
confirmation. No new training, authored descriptions/cases, source execution now,
protected/final-heldout access, catalog/ledger write, or live product change.
