# Interview question-bank intake

Hack2Hire problems, company reports, public descriptions, source categories and
LeetCode relationships in Gamma. [Browse the complete report](hack2hire/REPORT.md).

The 2026-10-28 listing contains **827 groups / 1,048 entries and variants**:

| Category | Groups | Entries / variants |
| --- | ---: | ---: |
| Coding | 604 | 805 |
| SQL | 109 | 129 |
| System design | 76 | 76 |
| ML system design | 19 | 19 |
| Object-oriented design | 19 | 19 |

Databricks has 15 coding groups / 20 variants, 10 system-design groups and one
ML-design group. The website sidebar uses variant totals for coding and SQL.
Company associations are Hack2Hire reports, not independently verified employer
statements. [The report](hack2hire/REPORT.md) lists every company and problem;
its acquisition section records current description coverage.

## Find problems

Run from the Gamma root; only Python's standard library is required:

```bash
python3 projects/question_bank/bank.py stats
python3 projects/question_bank/bank.py list --company Databricks --category coding
python3 projects/question_bank/bank.py list --company Databricks --category system-design
python3 projects/question_bank/bank.py list --topic rate-limiting
python3 projects/question_bank/bank.py list --title firewall --json
python3 projects/question_bank/bank.py list --leetcode 359
python3 projects/question_bank/descriptions.py show --id 6aa861578c97c56cdbdc93df
```

`show` reads the locally cached public description/preview; it does not generate a
solution. Coding variants retain separate identities. A group preview is linked to
its variants without being promoted into a complete variant-specific contract.

## Collect and rebuild

```bash
python3 projects/question_bank/bank.py fetch
python3 projects/question_bank/descriptions.py acquire
python3 projects/question_bank/descriptions.py index
python3 -m unittest discover -s projects/question_bank -p 'test_*.py'
```

`fetch` collects the public listing and official LeetCode title/ID/slug metadata.
It validates pagination totals, group/variant identities and source categories before
writing. Existing description-index metadata and manual reviews are reapplied by
source identity. A missing manually reviewed source identity stops refresh rather than
silently discarding the review.

`acquire` collects public `GET /algro/v1/post/POST_ID` responses, once per group and source version.
It spaces requests, honors Retry-After rate limits and resumes from a persistent
cache. Cached responses whose source update date differs from the listing are refreshed. `index` rebuilds searchable description metadata without network access.
These commands use no authentication, full-content, solution or execution endpoints.

Local source responses live in `data/question_bank/hack2hire/details/` and are ignored
by Git. The versioned description index holds short excerpts, hashes and provenance.
Another checkout can recreate its local source cache with `acquire`; versioned metadata
does not imply that the cache exists on that machine.

Signed-in access was verified in Chrome A (XY). Uniform Group Spanning Tree still
displayed Subscribe for full content. That does not block public description intake;
a preview's length or presence does not establish a full problem specification.

## Files and labels

- [bank.json](hack2hire/bank.json): all groups, variants, source links, company labels,
  frequency/difficulty, stages, source topics, description references and overlap candidates.
- [descriptions.json](hack2hire/descriptions.json): public-description excerpts,
  provenance, company attributes and explicit source LeetCode references.
- [fetch-receipt.json](hack2hire/fetch-receipt.json): listing request totals and hashes;
  these describe the listing fetch, separately from description acquisition and reviews.
- [leetcode-metadata.json](hack2hire/leetcode-metadata.json): official public titles,
  IDs and slugs, with no statements, solutions or evaluation payloads.
- [reviews.json](hack2hire/reviews.json): six original public Databricks variant synopses,
  source inconsistencies and a reviewed relationship to LeetCode 751.

Preserve original source titles, including spelling mistakes. The five top-level
categories and algorithm tags come from Hack2Hire. Additional description-topic labels
are keyword heuristics kept separately from source tags and verified requirements.
Source difficulty/frequency values retain their original scale without an inferred
interpretation. Last-reported dates remain source reports rather than freshness proof.

## LeetCode comparison and future solutions

The title pass uses 4,096 official public metadata records: seven exact-title candidates
and 34 possible title overlaps. Source descriptions additionally contain explicit
LeetCode links, indexed separately as related-problem citations. Neither evidence type
authorizes automatic merges. No title match does not establish novelty.

Equivalence requires comparing inputs, outputs, operations, constraints, ordering and
each variant. For example, IP CIDR Firewall cites LC 751 but has a different contract.
Two commute variants also contain example inconsistencies; their examples are not
trusted test oracles. Group previews alone may omit requirements needed for solving.

The collected descriptions support later original implementations. This intake imports
no solutions, admits no training/evaluation source, and changes none of Algorithm
Solver's frozen universes or protected evaluation populations. Qualification remains
separate from acquisition, categorization and overlap analysis.
