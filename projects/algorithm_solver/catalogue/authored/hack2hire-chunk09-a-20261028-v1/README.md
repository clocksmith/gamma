# Hack2Hire chunk09-a: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk09-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk08 and chunk09-b) are separate; this cohort follows the chunk07-a and chunk08-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and row formats is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Autocorrect Prototype is titled as autocorrect, but its
preview describes anagram lookup per query; the cohort follows the preview. Several previews stop before the part that matters
most: Validate Playlist Sequence stops before defining Shuffle and Random Mode; Bubble Explosion stops before the explosion
rule; CPU Usage Analysis and Caesar Cipher Rotation stop before saying what to compute; Account Registration Deduplication
and Best Meeting Date by Country stop before the output; Apply Domain Request Limits names the class but not its methods;
Asteroid Collision - Different Speed does not give the collision rule. The second and third levels of AI Token Billing
Calculation, Account Registration Deduplication and Build Smallest Number have no public text at all.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest the inferred
  domains allow is a billing total of about 2 * 10**14; the largest in the cases is exactly 2 * 10**14 + 10**6).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (sorted copy comparison, per-offset
  splitting, a full sort of every window, per-user and per-pair rescans with a linear plan lookup, linear scans over registered
  paths, quadratic scans over earlier accounts, per-call counting over all accepted requests, repeated pairwise collision scans,
  sorted-letter comparison per query, memoised recursion, per-country date rescans, literal grid rounds, permutation enumeration,
  per-peak counting, per-unit time marking, alphabet index lookups). `cases.py` generates small random rows, boundary rows and
  analytic rows at the inferred maximum bounds. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain
  rejections, a domain and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (2 variants: APIMatchingSystem, DomainRateLimiter) follow requested-22-a and chunk08-a: a module-global class
  (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)`
  trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to
  string uids, constructor arguments and void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy
  controls plus author-local runs.
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Valid Zero-Based Permutation Check: an empty list is a permutation (true). The preview allows in-place modification and asks
  for O(1) extra space; the cohort effects contract forbids input mutation, so the cyclic placement runs on a private copy and
  uses O(n) memory. This is a recorded deviation from the preview's space requirement.
- Validate Playlist Sequence: songs 1..numSongs; Shuffle Mode plays every song once per cycle; the observed window may start
  mid-cycle, so the answer is true when some cut offset leaves no repeated song inside any piece.
- Windowed Average excluding Largest K returns the floored integer average (toward negative infinity), not a float, so both
  languages are exact; equal values are excluded one at a time.
- AI Token Billing Calculation takes a `pricing` list (an inferred input). Level 1 prices input and output tokens per plan;
  level 2 adds a monthly fee and included free tokens per (user, plan), consumed in session order, input before output;
  level 3 adds a usage cap per (user, plan) that excludes the fee. Output is `[user_id, total]` sorted by user id.
- API Path Matching compares whole segments; "/" is registrable and an ancestor of every path; no wildcards.
- Account Registration Deduplication returns the ascending indices of duplicate accounts. Level 2 lower-cases emails, cuts the
  local part at the first "+", removes its dots, and keeps only the digits of phones.
- Apply Domain Request Limits: `DomainRateLimiter(maxRequests, windowSize)`, `allowRequest(domain)`; the i-th call is at
  second i; a request is accepted when the domain has fewer than maxRequests accepted requests in `(i - windowSize, i]`.
- Asteroid Collision - Different Speed: the sign of the speed gives the direction; LeetCode 735 structure (no same-direction
  overtaking); the larger momentum mass * |speed| survives unchanged; equal momenta destroy both. Output `[mass, speed]` pairs.
- Autocorrect Prototype returns, per query, the anagram words in input order with duplicates; the query itself counts.
- Ball Picking Game: a turn takes 1 or 2 balls from the left end or from the right end (not one from each); returns the first
  player's final score.
- Best Meeting Date by Country returns `[country, date, attendees]` sorted by country; countries with no dates are omitted.
- Bubble Explosion: a bubble with at least two same-colored orthogonal neighbours explodes together with them; explosions are
  simultaneous, bubbles then fall down, and rounds repeat until stable.
- Build Smallest Number: level 1 single digits (all zeros give "0"); level 2 whole non-negative integers concatenated, trying each
  distinct non-zero value as the first element (the comparator-smallest non-zero element is not always the best first one).
- Build the Longest Spike allows an empty increasing or decreasing side (a single number is a spike).
- CPU Usage Analysis: half-open time, the innermost open task runs, exclusive time summed per name, sorted by name.
- Caesar Cipher Rotation encodes with any integer shift, keeps case and leaves non-letters unchanged.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). There were no post-freeze amendments: the first full candidate run passed every row in
both languages.

## Local checks (author self-check, not qualification)

All 5167 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 40880 seeded Python rows matched the references. The native observers pass on all 509 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.48 s per execution under node --jitless and 0.21 s under
python3 (Windowed Average excluding Largest K, `checks.json`). These runs check the code against the author's own inferred
contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all, the
official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
