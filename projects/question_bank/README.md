# Interview question-bank intake

Source-linked Hack2Hire inventory, original summaries where reviewed, and conservative
LeetCode overlap candidates. [Browse the complete report](hack2hire/REPORT.md).

The 2026-10-28 public listing snapshot contains **827 groups / 1,048 entries and
variants**: coding 604/805, SQL 109/129, system design 76/76, ML system design 19/19,
and object-oriented design 19/19. Databricks coding contains 15 groups / 20 variants.
Counts reconcile with the website sidebar, which displays variant totals for coding
and SQL rather than group totals.

This inventory is complete at the listing level. Detailed acquisition is incomplete:
six public Databricks variants have original specification synopses, and 1,042 entries
have no acquired specification. The browser displayed Log In; its login route rendered
blank. No authenticated access has been established. The anonymous listing's lock
flags do not determine the user's subscription or access.

## Inspect and refresh

Run from the Gamma root; only Python's standard library is required:

```bash
python3 projects/question_bank/bank.py stats
python3 projects/question_bank/bank.py list --company Databricks --category coding
python3 projects/question_bank/bank.py list --overlap exact_title_candidate
python3 projects/question_bank/bank.py fetch
python3 -m unittest discover -s projects/question_bank -p 'test_*.py'
```

`fetch` reads the public, unauthenticated listing API across all five categories and
the official LeetCode public metadata endpoint. It checks pagination totals, duplicate
group/variant identities and source types before writing. It fetches no solutions,
LeetCode statements or authenticated data. Existing manual reviews are reapplied by
source identity, so a missing reviewed source identity stops refresh rather than
silently discarding the review.

## Data and classification

- [bank.json](hack2hire/bank.json): all groups, distinct variants, source links,
  companies, difficulty, frequency, source topics, normalized topics and acquisition status.
- [fetch-receipt.json](hack2hire/fetch-receipt.json): listing page counts and response
  SHA-256 hashes; official LeetCode metadata provenance. These receipts describe the
  metadata fetch, separately from subsequent public-page reviews.
- [leetcode-metadata.json](hack2hire/leetcode-metadata.json): 4,096 official public
  titles, IDs and slugs, with no statements, solutions or test payloads.
- [reviews.json](hack2hire/reviews.json): original public-page synopses, source issues,
  and a reviewed relationship between IP CIDR Firewall and LeetCode 751.

Preserve source titles, including spelling mistakes. Source topic labels are retained
verbatim and normalized separately. Missing topic labels remain empty; titles alone
do not justify inventing algorithm requirements. Source difficulty/frequency scales
are preserved without an inferred interpretation.

The lexical pass finds seven exact-title candidates and 34 possible title overlaps.
All have `merge_allowed: false`. No title match does not establish novelty; custom
interview titles frequently describe familiar concepts. An equivalence review must
compare inputs, outputs, constraints, operations, ordering and each variant separately.
IP CIDR Firewall is explicitly related to LC 751 but has a different contract; it is
not a duplicate. Two commute variants also have source example inconsistencies,
recorded in their review; those examples are not trusted test oracles.

## Remaining acquisition work

Verify authenticated browser access, then inspect accessible detail pages and preserve
variant-specific contracts through original summaries. Review the 41 title candidates
against full specifications and inspect custom-title problems for conceptual overlap.
Full-statement or solution redistribution rights have not been established. Locked
or incomplete descriptions remain explicitly missing; there is no access bypass.

This lane does not admit a training/evaluation source or qualify solutions. Algorithm
Solver's frozen universes and protected evaluation populations are unchanged. Intake
summaries are not executable tests, solver implementations or correctness evidence.
