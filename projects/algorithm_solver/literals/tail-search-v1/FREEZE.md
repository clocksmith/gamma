# tail-search-v1: syntax-cost search with alphabet and occurrence ablations

Board item 3, goals 2a/2b. Sources stay fixed; this changes conventional
vocabulary search, not decoder semantics or the M1 rules.
[Item A](../cost-decomposition-v1/README.md) measured syntax at 50.2% of L-R-256
selection cost and identifiers at 48.2% of its single-character tail. Syntax
fragments may include identifier bytes; exact decoding and every selected byte
remain charged. Neither A's optimistic oracles nor local search termination
establish attainable search headroom.

## Fixed inputs and exposure

The exact R dev-fit 300 / dev-val 100 and starting L-R-128/256 dictionaries are
inherited by hash from cost-decomposition-v1. The final held-out 100 and protected
66 remain closed. Historical dev-val measurements, including A, are development
feedback; no fresh generalization claim is made.

Only the 300 allowlisted fit sources enter candidate mining, alphabet choice or
search. The worker writes a final dictionary and `fit-seal.json` before it opens
any validation source. Then it parses the 100 unchanged validation programs,
without a refit or source repair. Unencodable programs stay in the denominator.
Do not call any historical all-500 loader or restart the old 80-problem search.

**Pre-freeze audit:** all 300 fit sources parse, have supported `solve` entries,
and contain 89 distinct characters. Thus an observed-character alphabet can
reclaim seven of the current 96 reserved entries. Neither starting dictionary
contains a complete solve definition or body in fit. This audit measured no
candidate dictionary or validation outcome. Six synthetic mechanism checks pass.

## Eight arms, two controlled factors

At each width (128/7 and 256/8), start from the same pinned L-R dictionary:

| Arm | Mandatory alphabet | Proposal policy |
| --- | --- | --- |
| control | Existing 96 characters | Existing chosen-parse spans |
| alphabet | The 89 characters actually observed in fit | Existing chosen-parse spans |
| positions | Existing 96 characters | Half existing spans, half all-position short fragments |
| joint | The 89 observed fit characters | Half spans, half all-position short fragments |

Reclaimed alphabets preserve the relative order of remaining characters.
Observed fit characters remain mandatory. No free escape, side dictionary,
per-program dictionary, source substitution or variable-width ID is introduced.
Underfilled dictionaries still charge their declared 7/8-bit width.

Search uses the existing matched80-v3 refill/local-search implementation with
exact add/delete/swap/paired-move costs and unchanged canonical segmentation.
Changing a mandatory alphabet is an explicitly isolated policy factor. Each arm
has 60,000 exact dictionary trials and a 900-second safety cap, including mining
in the timed search phase. Early local termination is reported as local only.
The incumbent cannot worsen on fit; validation may worsen.

All arms first refill any free slots (24-entry shortlist), then use the same
neighborhood: 96 addition candidates, 500 swaps, 16 pair additions, eight pair
removals, 150 paired moves. No random kicks or learned ranker.

## All-position proposer

Mine every fit substring of lengths 2 through 24 that contains at least one
syntax-labelled byte. Keep only strings witnessed in at least two distinct
fit programs. For each length range 2–4, 5–8, 9–16 and 17–24, retain at most
1,024 by summed occurrence count times `(length - 1)`; ties use length/text.
The resulting at-most-4,096-string pool is fixed for that arm. Pool and
occurrence mining time is charged. These are bounded proposals, not an
exhaustive dictionary optimizer.

In each round, distribute each currently selected token's unit charge uniformly
across its bytes. Score a proposed occurrence as positive fractional cost minus
one, only when it intersects a current single-character syntax selection.
Sum these heuristic scores (overlap may overcount); round to nine decimals for
deterministic ranking. Use half the shortlist for existing span proposals,
then ranked short fragments, then unused old proposals if there is room.
This ranker can propose fragments beginning/ending inside current parse tokens.
**Only exact whole-source resegmentation decides whether to accept a move.**
Scores are neither lower bounds nor realized savings.

Exclude exact complete source, solve definition, solve body (with or without
braces) from all newly proposed entries. A final audit against fit and validation
rejects a candidate containing any such entry; validation never repairs it.
This is a concrete whole-solution exclusion, not a BITS macro-classification claim.
All source strings, vocabulary entries, sequences and traces remain private.

## Measurement and checks

Every encoded source must decode independently through the canonical codec to
its pinned hash. Source semantics are unchanged, so prior qualification is
reused; no fresh source execution or unseen solving is claimed. No source
rewrites or sandbox campaign are needed for this fixed-source comparison.

Report per arm and split: coverage with all failures, total/median/p90/p95/worst
selections and complete actions, <=32/96 counts, single-character fraction,
syntax/identifier/literal attribution, dictionary bytes, packet headers/padding,
complete package bytes, trial count, stop reason and measured wall time. Finish
costs one action per encoded program; navigation/correction costs are zero.
The 41-byte headers and fixed-width payload are encoded by the canonical codec.
Full interpreter/runtime storage is unmeasured and does not disappear into zero.

Paired validation comparisons use all 100 IDs and the frozen baseline. A failed
encoding is a regression and blocks readiness. Record worse/same/better counts,
not just averages. Separately compare each policy against the matched searched
control to distinguish baseline continuation from the proposed factors.

Before launch: Python compilation/import and six synthetic tests; retain A's
37 passing judge/lane checks (no judge or lane code changes in this stage).
Commit/push this freeze and contract, ask Claude to review, and wait for reply
or PLAN's documented 30-minute timeout. Four search workers, no sandbox workers;
4 GiB per-process address-space cap, 2,400-second overall wall cap. Check host
load and BOARD first; preserve all partial outputs/failures.

## Predictions and readiness (unchanged M1 gates remain separate)

- T1: matched control cannot worsen fit and changes validation total by <1%
  from the pinned baseline at both widths.
- T2: alphabet alone lowers validation actions by at least 3% at 128 and at
  least 1% at 256; seven additional slots should matter more at the smaller cap.
- T3: positions improves fit at at least one width, but by less than 5%.
- T4: joint has fewer validation actions than either single factor at 256.
- T5: every arm encodes/decodes all 400 programs, with no whole-solution entries.
- T6: no arm satisfies all M1 cost indicators on dev-val; this is not the 500
  qualification even if the indicators happen to pass.

A candidate is development-ready for a separately proposed confirmation only if,
against the pinned L-R baseline at its width, all of these hold:
1. 100/100 validation programs decode, and whole-solution audit is clean.
2. Total actions fall at least 5%; median and p90 actions both fall.
3. At least 60 programs improve and at most 25 worsen.
4. Single-character fraction does not increase and dictionary-plus-packet bytes
   stay within 105% of baseline.

Pick the ready arm with least validation actions, then least package bytes,
then lexical arm name. Reporting each factorial contrast remains mandatory.
Readiness authorizes no final-held-out opening, source publication, BITS deploy,
training, human study or M1 claim. A negative result is recorded, then board
item 4 proceeds with a new source-rewrite freeze. Any later scorer proposal
still needs demonstrated conventional-search benefit and owner approval.

Component intent preserved: algorithm_solver literal research, with no new
production boundary, catalog/ledger/claim write or autonomous generation route.
