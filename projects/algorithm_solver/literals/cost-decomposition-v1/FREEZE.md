# cost-decomposition-v1: fixed-source costs and optimistic dictionary bounds

Item A, owner direction of 2026-10-23; goals 2a/2b. This is a diagnostic,
not a rewrite, trained scorer, M1 qualification, or autonomous assembly run.
[contract.json](contract.json) pins code, the two current L-R dictionaries,
and the exact R sources for dev-fit 300 / dev-val 100 before execution.
No source text was inspected to design this stage. Historical source exposures
remain as recorded in roles-v1. The final held-out 100 and protected 66 stay closed.

## Inputs and execution

Use only the 400 allowlisted R paths and hashes copied from minify-control-v1.
Do not call its all-500 `pools()` loader. Reuse the roles-v1 L-R-128/256
codebooks, fitted on dev-fit. Do not refit, select sources or alter programs.
The current baseline is 14,014/8,948 dev-val selections, or 14,114/9,048
complete actions including one Finish per program. Retain selections and
actions separately; M1's existing selection thresholds do not change.

At most one analysis worker, 2 GiB address-space limit, 20-minute wall cap.
No sandbox source executions: unchanged source hashes reuse the existing
qualification; newly encoded packets must independently decode exactly through
the canonical codec. Run the charter's focused judge/lane checks and synthetic
bound/attribution checks before execution. Check host load and BOARD first.
Commit and push this freeze and implementation, request Claude's review in LOG,
and wait for reply (or the PLAN's documented 30-minute review timeout).

## Cost attribution

Acorn parses each allowed source without execution. ASCII-only input is
required so parser offsets equal byte offsets; drift fails closed.
Identifiers include variable/function names and property names. Literal spans
include numeric, string, regex, Boolean, null and template-content tokens.
The remaining syntax is split into keyword, operator, delimiter, layout and
comment. This is lexical attribution, not an assertion of semantic roles.

A selection overlapping categories contributes its byte fraction to each;
fractions sum to precisely one selection. Also publish an integer exclusive
partition (single-category or mixed), source bytes per category, and the exact
integer single-character tail per category. Do not count a mixed selection in
full in several categories or call the fractions counterfactual savings.
Aggregate syntax subcategories when comparing identifiers/literals/syntax.
Report both splits, totals, median/p90/p95/worst, <=32/96 counts, payload,
padding, 41-byte headers, dictionary bytes, packets and package bytes.
Finish is one additional action; navigation/corrections are zero for this
already-final sequential stream. The canonical codec's two source files are
reported separately by byte count; this is not its full interpreter footprint.

## Optimistic bounds and their exact scope

No general compressor is used as a lower bound. The sources are fixed; none
of these bounds applies to all equivalent programs permitted by goal 2b.
Whole-solution entries are prohibited in legal dictionaries, so every complete
program needs at least two literal selections, plus Finish. Existing legal
baseline dictionaries retain their provenance; no oracle output is promoted.

**Capacity-aware necessary bound for arbitrary exact strings.** On the fixed
400 development sources, let `b_p` be minimum selections when *every* substring
that appears in another development program and *every* individual character
is available. Each use costs one selection. Compute these paths exactly using
cross-owner suffix matches; no length cap or mined-candidate shortlist.
Impose the necessary two-selection floor. This oracle optimistically permits
whole bodies/foreign complete sources, unlimited shared vocabulary and free
availability of characters (character uses still cost selections).

For any actual single shared dictionary of at most K entries, at most K programs
can use a multi-character string that appears in no other program: each such
private entry belongs to one program. Every other program costs at least b_p.
Thus a necessary lower bound is obtained by lowering the K largest b_p to 2.
This is a simultaneous lower bound on total and sorted counts, hence median
and p95; the optimizing dictionaries need not be attainable or the same.
Compute K=128 and K=256. All dictionary entries remain bounded in the real
problem; the relaxation uses the capacity only to bound private-program
exceptions and drops competition for shared slots. Giving all K slots to those
exceptions while also granting unlimited shared strings is intentionally
optimistic. Do not mistake the oracle for a feasible <=256-entry codebook.
Fallback's only universal bound here is zero. Charge one Finish to the action
bound; packet/storage overhead is additional, never a reduction in selections.

**Fit-only substring transfer oracle.** Allow every substring witnessed in the
300 fit programs plus characters, then exactly parse dev-val and impose the
two-selection floor. Shared capacity and whole-body exclusion are relaxed.
This is a lower bound for the fit-witnessed-string policy only: a hand-designed
literal absent from fit can beat it. It is not a universal M1 bound. It measures
whether lack of repeated surface text alone explains baseline cost.

The cross-program oracle is retrospective development analysis, including
validation text; it must not be reused as a fit-only vocabulary or presented as
untouched validation. No source, dictionary or sequence is published: evidence
contains only IDs, hashes, counts and aggregates.

## Predictions and decision rule

- A1: Both baseline dev-val totals reproduce exactly (14,014 and 8,948).
- A2: Syntax is the largest byte-fraction selection category and the largest
  single-character selection category for L-R-256 on dev-val.
- A3: The fit-only transfer oracle's dev-val median is below 32 selections.
- A4: The arbitrary-dictionary capacity bound does not exclude median <=32
  and p95 <=96 on the fixed 400. This is inconclusive, not feasibility proof.
- A5: All 800 baseline packets decode to their pinned source hashes.

Acceptance requires exact decode, attribution conservation, reproduced totals,
synthetic exhaustive checks of the capacity argument and oracle matching,
and no out-of-allowlist source loads. Failures stop reporting of valid results.
No vocabulary promotion is possible in this diagnostic. Identify the largest
remaining measured category and tail, then freeze the next board experiment
against it; ties use syntax, identifier, literal order. Negative predictions
remain recorded. A useful gap motivates stronger conventional search; it
neither authorizes training nor proves that a learned scorer has headroom.

M1 unchanged; no final confirmation, BITS change, ledger/catalog/claim writes,
human study, training, or private-source publication. Component intent and
production boundaries are preserved.
