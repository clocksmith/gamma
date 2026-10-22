# M1 admission: the path to a frozen 500-problem population

Owner-approved on 2026-10-22 ([MILESTONES.md](../MILESTONES.md#owner-decision-2026-10-22)).
This stage lists the 363 metadata-eligible JavaScript problems, qualifies the 213 beyond
the current 150 in the literal harness, and plans the 137 newly written problems that
complete 500. The protected 66-problem reservation stays closed. No M1 threshold changes.
No corpus ledger, claim or catalog is written: admission here means admission to the
literal development population. Every problem is previously consumed corpus material,
never unseen.

## 1. The 363 and what each still needs

[`inventory.py`](inventory.py) rebuilds the published count from its three sources: complete
JavaScript entries in the revision-1810 ledger checkpoint (sha256 `7a1cdcc6…`, verified),
the qualified development catalogs, and the current 150. Union minus the protected 66:
**363**, of which **213** are beyond the 150. The script that produced the earlier count
was not preserved; this reconstruction matches it exactly.

Per-problem results: [evidence/admission-inventory.json](evidence/admission-inventory.json)
(IDs, keys, families, difficulty, hashes, check results and remaining needs; no source or
case content).

| Check (read-only) | Passing of 213 |
| --- | ---: |
| Admitted source present and hash-bound (211 normalized ledger artifacts, 2 catalog sources) | 213 |
| Execution receipt hash-bound and fully passed (public, independent, mutation, alias, sandboxed, no expected outputs in sandbox) | 213 |
| Standard and review receipts and campaign contract hash-bound (ledger route) | 211 / 211 |
| Five-family source seal binds source and case hash (1464, 1748) | 2 / 2 |
| Independent case file present, hash-matched, count-matched, harness shape | 213 |
| Outside protected IDs, protected families and protected near duplicates | 213 |
| No repeated key or identical source across the 363 | 213 |
| Entry point found in source (211 `class Solution` methods, 2 named functions) | 213 |

Difficulty of the 213: 43 easy, 150 medium, 20 hard (the 363: 122 / 204 / 37). Comparison
mode is `return` for all; 2 use list-node and 2 tree-node encodings, which the harness
already supports. Six family pairs hold distinct numbered problems (for example meeting
rooms I and II); they are distinct specifications, not paraphrases, and are kept.

**What each still needs:** all 213 need literal qualification (original oracle on every
independent case, recording result, type, mutation and alias baselines). Two (148, 1171)
also need the exact `ListNode` constructor appended and charged, as scale150-v1 did for
`TreeNode`. Nothing else failed.

The ledger has since advanced to revision 1873 (five more JavaScript completions: 773, 781,
790, 1252, 1266; 55 more entries claimed by another owner). Those five are outside the
approved revision-1810 inventory and are not added here.

## 2. Admission qualification stage (frozen before execution)

[evidence/stage-freeze.json](evidence/stage-freeze.json) (sha256 `5811a58f…`) binds the 213
IDs, source and case hashes, code hashes, Node v22.22.1, limits and the pass rule before any
candidate ran in the literal harness. [`stage.py`](stage.py) runs it with the scale150-v1
harness (byte-identical copy) and oracle rule ([`qualify_rules.py`](qualify_rules.py)):
batches of 16 cases, bwrap sandbox, 3 CPU s, 8 s wall, 1 GiB, four workers, one-hour stage
budget. `class Solution` sources run through `(...a)=>new Solution().<method>(...a)`.
Mechanics were checked beforehand on development problem 136 (already admitted): 108/108,
with a wrong-method negative control failing.

A failing problem stays in the 363 denominator with its logs and is not replaced; at most
one separately frozen packaging or adapter repair may follow.

**Result: 213 of 213 admitted** ([evidence/admitted-213.json](evidence/admitted-213.json)).

| Attempt | Problems | Qualified | Cases passed | Wall time |
| --- | ---: | ---: | ---: | ---: |
| 001, frozen stage ([report](evidence/qualification-attempt-001.json)) | 213 | 207 | 20,184 / 20,260 | 27.6 s |
| 002, exact-integer transport ([contract](evidence/repair-contract-002.json), [report](evidence/qualification-attempt-002.json)) | 6 | 6 | 553 / 553 | 1.1 s |

The six attempt-001 failures (633, 670, 738, 868, 989, 1056) are the problems the corpus
qualified under exact-integer runtime profiles. The literal harness passed every integer as
a JSON Number, which loses precision above 2^53−1 (and 633's source takes BigInt). Attempt
002, frozen and committed before it ran, changes input transport only: 633 receives BigInt
and the other five receive BigInt above 2^53−1, decoded by
[`harness-exact-integer.cjs`](harness-exact-integer.cjs), which differs from the frozen
harness by one decoder line. Sources, cases, expected values and the oracle are unchanged;
attempt 001 is preserved. Later rewrite experiments must run these six with the same
transport.

The 363 are therefore all qualified literal development problems: the 150 earlier stages
plus these 213. This is representation material with prior exposure, not unseen data.

## 3. Gap to 500: 137 newly written problems

[`gap.py`](gap.py) froze the selection before any solution was written
([evidence/gap-selection.json](evidence/gap-selection.json)). Eligible problems are pending
at both revision 1810 and the current snapshot (1873), unclaimed, unreserved, functional,
outside the protected IDs and families, outside the 363 and their families, and have a
hash-valid independent set of at least 20 cases: 1,503 problems.
[Amendment 001](evidence/gap-amendment-001.json), made before any solution was written,
skips problems whose cases expect non-finite values (Python `inf`), which the frozen harness
rejects whatever the solution: 3132 and 2817 (both medium), replaced in order. Quotas follow the 363's mix:
**46 easy, 77 medium, 14 hard**. Order within each stratum is sha256 of the seed
`gamma-admission500-gap-v1` plus the problem UID; the first quota are selected and the next
three times quota are the replacement order.

Each new solution is qualified the same way as the admitted corpus:

1. The writer sees the statement, signature and public examples only. Independent cases,
   expected outputs and stored reference solutions are not shown.
2. Source follows the corpus standard: a named implementation with a `class Solution`
   forwarding method, no injected helpers (a charged constructor line where a node type is
   needed), no expected-output special cases.
3. Execution in the sandbox: all public and independent cases pass, with expected values
   host-side; inputs are preserved unless the problem requires mutation, and returned
   values do not alias inputs unless required.
4. Literal-harness qualification under the stage-2 rule.
5. An independent review of the source against the statement for hard-coding or
   test-specific branches.

There is one submission per problem after public-example iteration. A problem whose
submission fails independent cases is recorded as failed, with logs, and replaced by the
next problem in its stratum's order. Independent-case feedback is never used to repair a
solution.

**Result: 137 of 137 written and qualified** ([evidence/gap-outcomes.json](evidence/gap-outcomes.json),
contract [evidence/gap-contract.json](evidence/gap-contract.json)). Writers made 174 submissions, one
per problem. 137 passed all public and independent cases and an independent source review;
37 failed and were replaced in their stratum order. By difficulty: easy 46 of 56, medium 77 of
97, hard 14 of 21. Failure causes, from a host-side diagnosis that was never shown to writers:
28 wrong answers (most on one to six cases), 7 runtime errors and 2 time limits. Two failures
come from the test data, not the writing: 1592's public examples collapse runs of spaces, so no
statement-correct output matches them; 784's statement allows any order, but its cases compare
one order exactly. No review rejected a passing source. The frozen harness also caps the V8 heap
at 64 MB (`--max-old-space-size=64`). Later writers were told so; the 363 admitted sources passed
under the same limit.

## 4. The frozen 500

**Frozen 2026-10-22** ([evidence/population-500.json](evidence/population-500.json), sha256
`0d6cb3ff…`), before any M1 measurement on the 213 admitted or the 137 new problems.
[`freeze500.py`](freeze500.py) bound it: the 150 earlier development problems, the 213 admitted
here and the 137 newly written. That is 168 easy, 281 medium and 51 hard, with 48,405 corpus
cases. Each problem records its admitted source hash, charged helper bytes, entry form, transport
(9 exact-integer), adapter (23: nested list nodes; 30, 78, 90: unordered outer order), and case
count and hash. All 500 admitted sources pass all 48,405 cases in the frozen harness.

Requirements for any successor source: the unchanged oracle on every case; strict parity with
the admitted source's result, type, arguments after the call and alias edges; exact integers;
and the stage resource limits (finite tests, not a complexity proof). All 500 stay in the M1
denominator. M1 still needs 400 of 500 at the unchanged compactness gates. The protected
66-problem reservation was never opened.
