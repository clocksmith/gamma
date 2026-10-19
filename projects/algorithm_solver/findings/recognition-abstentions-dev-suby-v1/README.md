# Nine recognition abstentions: trace diagnosis and proposed comparison

This is deterministic diagnosis of the completed
[recognition reconstruction pilot](../recognition-rebuild-dev-suby-v1/README.md),
not a new inference, judge run or accuracy result. The
[hash-bound diagnosis and exact proposal](diagnosis-and-proposal.json) retain the
nine first choices, scores, reasons and contradiction-only candidate lists. The
control remains immutable at candidate SHA256
`64f10768b5004782cf8549215357d8d08ee2be8cd74b8b6198fe8c7ced83a33e`.

## What failed

The four `identity_not_confident` cases split into **three absolute-score failures
and one margin failure**. The score floor stays `0.634824546178182`; the general
margin stays `0.004102371987842357`, and the sibling margin stays `0.02`.

| Request | Retained evidence | Diagnosis |
|---|---|---|
| pair-unsorted | Sorted/one-based Two Sum II first, 0.788877; intended unsorted/zero-based source second, 0.725135. Public check: 0/3. | Selection ignores explicit ordering/indexing contradictions. Public rejection correctly prevents a wrong answer. |
| houses-line | Circle first, 0.725761; line second, 0.707546; sibling gap 0.018215. | Explicit straight-street layout is available but unused by the margin-only guard. |
| houses-ring | Correct circle first, 0.720523; line second, 0.711911; sibling gap 0.008612. | Explicit circular adjacency is available but unused. |
| stock-once | Unlimited trades first, 0.698472; one trade third, 0.670505. Public check: 1/2. | Selection ignores the explicit one-transaction limit. Public rejection correctly prevents a wrong answer. |
| stock-fee | Correct fee source alone after interface filtering, 0.627357. | Absolute score is 0.007468 below the floor; a contradiction filter cannot fix it. |
| stock-rest | No-cooldown first, 0.709580; correct cooldown second, 0.707140; gap 0.002440. | Explicit one-day cooldown is unused; the general margin fails. |
| courses-order | Correct ordering source first, 0.622252. | Absolute score is 0.012572 below the floor, despite an explicit output distinction. |
| islands-area | Unapproved bordered square first, 0.811851; intended component area fourth, 0.732229. | Semantic ranking error plus deliberate qualification policy. Removing square output still leaves an unprofiled, unapproved closed-islands source ahead. |
| ranked-value | Correct duplicate-counting batch rank source first, 0.510923. | Absolute score is 0.123902 below the floor. The grammar already recognizes the relevant rank/duplicate/batch distinctions. |

Five cases expose unused explicit requirements; three expose score calibration or
representation limitations. The island case combines ranking limitations,
partial requirement representation and intentional qualification policy. None of
these traces demonstrates genuine user underspecification as its primary cause.
Missing parser facts are not proof of ambiguity. For example, the island grammar
extracts area but misses the land family because its only literal occurrence is
negated; mutation permission remains unknown and must not be invented. The
stock-fee grammar also misses an output-profit phrase, although it recognizes the
fee. No new grammar rule or profile has been fitted to these requests.

The eight requests without public examples remain **pre-retrieval gate evidence**;
they do not demonstrate semantic absence or ambiguity detection. Source approval,
public execution and all numeric gates behaved fail-closed. Those safeguards are
not defects to remove.

## Smallest proposed candidate

`recognition-requirements-dev-suby-v1` adds a contradiction-only filter before
confidence/identity selection. The existing text-only query grammar supplies
explicit facts and evidence spans. Existing curated source profiles bind through
the exact source-statement SHA256: 22 of the 66 indexed entries have matching
profiles from the frozen 24-profile catalog. These are curated development
metadata, not automatic semantic proofs. Parsing both sides with the current
query grammar is insufficient: most original source statements yield sparse
facts.

Compare only known, explicit facets: ordering, indexing, layout, transaction
limit, fee, cooldown, output, updates, duplicates and allowed changes. Do not use
family tags to exclude entries. A contradiction removes a candidate; silence,
unrecognized text, missing profiles and stale hashes remain unknown. Conflicting
query facts abstain. Unprofiled and unapproved candidates stay visible. Preserve
scores, cosine and relative order; use the same thresholds and approval manifest.
Exactly one choice reaches the public judge, and failure abstains. Do not search
through candidates using public-test outcomes.

Computing the existing margins over the compatible list is an explicit policy
change that needs regression checks. Preserve original margins and first choices
in evidence. A partial compatible profile does not establish equivalence or
supply a missing requirement. Exact lookup and the default control stay unchanged.
No oracle target key, source text, starter, signature, hidden output or test-suite
result enters the query parser. Source hashes bind offline metadata only.

The retained-list counterfactual changes first choice or removes the contradictory
sibling for the five requirement cases. It does not establish accepted correctness
or a new score. The three below-floor cases remain blocked. The island case still
has an unprofiled/unapproved leader. No numerical coverage improvement is claimed.

## Exact next comparison and stop point

The JSON proposal fixes the same **66 entries, 24 inputs, 66 vectors and 16-source
approval manifest**, with their hashes. First implement the opt-in policy and test
unknowns, negation/conflicts, stale bindings, stable scores, unchanged gates,
public-failure abstention, exact lookup and control preservation using synthetic
renamed entries. Inspect the bound source facts without adding profiles or tuning
rules to these nine cases. Then seal the implementation and complete candidate
contract before any inference. This report freezes the design and input bindings;
it is not an implemented-candidate seal.

A subsequent matched run records one shared query embedding/raw retrieval list
for both arms, charges its cost to both, and saves full raw and filtered decisions.
Alternate arm order by fixed request position. Seal all public decisions before
independent scoring; publish all 24 dispositions, first-choice errors, useful and
harmful changes, wrong/unqualified answers, abstentions and complete costs. The
old traces retain only post-interface candidates, so the counterfactual cannot
replace that instrumented comparison. Preserve atomic, hash-bound resumption and
`sandbox_error` for infrastructure failures.

Use the existing four CPU threads, 8 GiB RSS, 5 GiB disk and 900-second first-run
wall cap. No downloads, training, new framework or protected scoring. All raw
source, tests and code responses remain local and ignored. No model run or new
sandbox execution occurred during this diagnosis. No application test suite was
run for this report-only change; validation is trace/hash consistency, diff and
local-link inspection.

This is consumed development evidence with no release promotion or fresh
confirmation claim. The existing zero-question and no-generated-source contracts
remain intact. The three score failures need a separate representation proposal;
full historical recognition and original composition assets remain unavailable.
The next action is implementation and deterministic checks, followed by a new
candidate seal; this turn stops before further inference as requested.
