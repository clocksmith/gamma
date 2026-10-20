# Bilingual corpus campaign: first reviewed batch and complete accounting

This historical checkpoint is followed by the [33-pair checkpoint](../corpus-campaign-128-v2/README.md).

The campaign covers 2,354 eligible problems /4,708 problem-language entries.
The first 11 problems now have 22 selected normalized implementations, each with
unchanged public/independent execution, structural enforcement, mutation/alias
checks and separate semantic/complexity review. Per language:958 independent
cases +27 public cases =985 passed;1,970 selected normalized executions total.
Historical failures remain in immutable attempt records. Existing baseline
qualification remains 2,354 Python /94 JavaScript and is not conflated with
normalization completion. No production catalog or autonomous-composer promotion
is implied. New normalized JS sources require their own later catalog integration.

| Problem | Cases per language | Selected implementation |
| --- | ---: | --- |
| 148 | 112 | Bottom-up stable linked-list merge; corrected empty helper |
| 153 | 98 | Approved original search semantics with half-open bounds |
| 242 | 109 | Unicode-codepoint counting; no normalization/case folding |
| 300 | 137 | O(n log n) tails/lower-bound, replacing Python quadratic DP |
| 347 | 36 | O(n+U) stable frequency buckets, first-appearance tie order |
| 387 | 94 | Lowercase counting with exact original-domain behavior |
| 532 | 129 | Deduplicated fixed-difference endpoint counting |
| 537 | 64 | Parsed complex-number multiplication |
| 539 | 86 | Sorted parsed minutes, preserving original compatibility |
| 541 | 106 | Alternating half-open block reversal |
| 544 | 14 | Seeded tournament pairing |

These are development reference results. Tests do not prove universal correctness.
Complexity assumptions and input domains are per-source declarations. #539 uses
the pinned runtime's comparison sort; no JS language-level sort bound is claimed.
Unicode regression probes for 242, linked-list helper/boundary probes and checker
unit tests are separate software checks, not extra independent solving cases.

## What the 3353-to 2354 filter actually means

The full known-answer corpus contains 3,353 problems with statements and stored
Python sources. A separate experimental retrieval/training list intentionally
excludes solving-test pools and nearby duplicates. Intersecting them removes 198:
193 excluded solving-pool slugs and 5 frozen near-duplicates. All 198 have sources,
197 have public examples, and 31 already have independently qualified Python
solutions. Their exclusion is an experiment boundary, not proof of inability.

From the 3,155 remaining entries,685 lack the existing approval record. Approval
is a recorded evidence gate: identity/provenance/interface metadata are valid,
the selected source hash matches, the stored solution passes positive independent
test verdicts, and the checked exact-answer route returns that correct source.
It is not a new permission request. The 685 recorded reasons are:

| Reason | Count |
| --- | ---: |
| Missing independent tests | 518 |
| Exact-answer route not qualified | 70 |
| Protected composition aliases | 65 |
| Unusable imported evidence | 19 |
| Failed validation | 11 |
| Unusable independent tests | 2 |

That leaves 2,470. Further frozen-boundary closure removes 116:9 audit-family
entries,105 recognition-family entries and 2 nonresearch aliases. This leaves
2,354; unique numeric identity and positive-test-set checks remove no more entries.
The narrow composition reservation contains 66 keys/60 families;65 keys occur in the
full 3,353 corpus and one lies outside it. Across all current research boundaries,
381 of the 999 excluded entries touch a frozen boundary. The other 618 are recorded
in a separate qualification backlog:516 missing independent tests,70 exact-answer
route failures,19 imported-evidence repairs,11 failed validations and 2 unusable
test sets. This preserves the objective of completing all known problems without
silently admitting held-out solutions into research/training. The broader imported
problem metadata contains 4,081 distinct numeric LeetCode IDs; it is a different
population from the 3,353 entries with statements and references.

Exact counts, provenance hashes and code pointers are in `count-funnel.json` and
`exclusion-audit.json`. This audit read metadata, not protected case contents.

## Resume and remaining work

The live private ledger is
`/home/x/Documents/Codex/2026-10-19/task/corpus-campaign-v1/ledger.json`.
A frozen copy and content-addressed receipt artifacts are preserved under
`runs/corpus-campaign-128-v1/`. Do not create two concurrent ledger writers.

```sh
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign \
  --ledger /home/x/Documents/Codex/2026-10-19/task/corpus-campaign-v1/ledger.json status
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_campaign \
  --ledger /home/x/Documents/Codex/2026-10-19/task/corpus-campaign-v1/ledger.json next --limit 10
```

Claim an eligible entry with the returned revision and owner; preserve original
sources, freeze its candidate/contract, execute all unchanged cases in the existing
sandbox and obtain independent review before recording completion. The CLI
requires current revisions, exclusive family claims, unchanged source/test hashes
and complete evidence. See `../../contracts/corpus_campaign_v1.md`.

Remaining after this batch:4,686 implementations across 2,343 problems.100 W002
problem deliveries remain outstanding;36 additional alias-reserved problems are
also protected from competing claims. Delivered originals are reconciliation work,
not automatic qualification. The verified 150 W002 source hashes match the prior
Mac inventory; no wholesale overwrite or public push was performed.
