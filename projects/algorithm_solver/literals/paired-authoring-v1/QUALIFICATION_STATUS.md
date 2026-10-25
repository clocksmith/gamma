# Dot qualification checkpoint, 2026-10-25

[Aggregate receipt](qualification-summary.json) binds private complete evidence.
The frozen population remains 500; the permitted development slice remains 400.
Final 100 and protected 66 remain closed. **M1 is not met.**

## Actual execution

The original 400 JavaScript programs were replayed through the approved pinned runtime,
with historical typed/exact-integer transports and independent host-side oracle
and full observation parity. 397 passed; 1015, 1079 and 1088 exhausted the unchanged
CPU budget. Those failures remain recorded, not relabeled semantic errors.

Three fully charged, independently replayed source successors restore coverage:
- 1015 uses multiplicative order of 10 modulo 9k, exact integer modular powers
  and factor reduction, rather than an O(k) remainder walk.
- 1079 counts distinct sequences by length and binomial interleavings instead
  of enumerating every sequence.
- 1088 counts valid-digit integers and subtracts rotation-invariant integers,
  enumerating only half-length digit choices.

Together, the 397 unchanged originals and these three successors pass all
**39,368 frozen development cases** across **400 JavaScript programs**. Fresh independent
small-domain controls also pass **4,240 checks** in both languages. Verifiers
replay actual outputs and hashes; pass flags alone cannot establish eligibility.
This is finite behavioral evidence, not a proof beyond declared domains.

166 additional JavaScript alternatives pass as complete source plus a charged
`solve` adapter. One adapted alternative (#78) failed strict historical parity
and stays ineligible. Prior candidate failures, unresolved domains and resource
failures remain available in private evidence; no case values or private original
sources are published. Repairs to #66, #582, #599, #910 and #922 were independently
replayed after preserving earlier failures.

## Remaining M1 work

Source/dictionary fitting must preserve legal literal entries, charge every helper
and adapter, compare 128/7 and 256/8, and meet median 32, p95 96 and 10% character
bits. A previous bounded fixed-source search was negative. The next hypothesis
jointly chooses qualified sources and reusable complementary small/medium literals.
All dictionaries and selection procedure must freeze before held-out scoring;
400-program runtime coverage alone is not an all-500 compactness result.
