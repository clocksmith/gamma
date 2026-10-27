# Coverage diagnosis before another fit

`coverage_diagnostics.py` explains retained dictionaries or audits the full current
candidate pool. It never fits a dictionary, rewrites a source, executes a candidate,
assigns a split or creates qualification. Source acquisition uses the same pinned
fitting-input owner and live per-open service gate. Keep private output outside
public Git: it contains per-source hashes, offsets and hashed missing spans.

The Acorn observer optionally emits code-point token intervals/categories and
descriptive structural features, without token values. Default fitting output and
proposal behavior are unchanged. Whole lexical boundaries remain enforced for
human-oriented pools; compression controls retain their separate policy.

```sh
python3 projects/algorithm_solver/literals/joint-v1/coverage_diagnostics.py \
  --config /absolute/private/fitting-config.json --config-sha256 CONFIG_SHA256 \
  --node /absolute/existing/node --node-sha256 NODE_SHA256 \
  --comparison /absolute/private/retained-comparison \
  --comparison-pool-sha256 RETAINED_CANDIDATE_POOLS_SHA256 \
  --output /absolute/private/new-diagnostic
```

For current proposals, replace the comparison arguments with `--pool-only`.
Retained pools are independently pinned and checked against actual source witnesses;
they are not silently replaced by a newer miner. Pool-only mode records no selected
dictionary and cannot report a measured search gap. A supervisor must enforce a
wall bound and the applicable memory policy. Each source is limited to 32768 code
points and 200000 matching occurrence edges per graph; exceeding a limit fails
explicitly. Sampled RSS monitoring is not a hard aggregate memory cap.

## What the evidence means

- Full-pool parsing is an unlimited-dictionary relaxation. Failure explains this
  pool; it is not an impossibility result for all legal literals or programs.
- A complete minimum-selection path using at most K distinct entries is an
  individual constructive witness. An over-budget minimum path does not prove
  infeasibility: a longer path can use fewer distinct entries.
- A character covered by only one candidate literal forces that literal. For
  alternatives, intersect forced sets before unioning across problems. This is a
  necessary shared-entry lower bound for the full-pool-representable subset.
- Unioning one complete path per problem gives a constructive shared-entry upper
  bound for that subset. A lower bound below K and upper bound above K leave the
  K-entry question unresolved. Neither bound drops failed programs from the full
  denominator or establishes compactness/human usability.
- Unsupported spans distinguish identifiers, numbers, keywords, strings, regular
  expressions, operators, syntax, comments and layout. Every-character occurrence
  coverage can still fail to form a connected segmentation; the diagnostic reports
  this separately rather than treating covered positions as a complete program.

## The retained 250-source failure

The [retained-pool audit](development-replay-v1/retained-coverage-diagnostic.json)
rechecks the original constrained comparison on the same 250 exposed JavaScript
fit sources. The combined human pool with punctuation fallback can represent only
127/250 even with every candidate available. Of the other123,102 lack candidate
text,9 fail only because of lexical boundaries, and12 have overlapping occurrences
but no complete path. At eight bits,43 are selected and84 uncovered programs have
individual <=256-entry witnesses. This is not a shared-dictionary feasibility proof.

For that combined pool, unsupported character counts are165 identifier,339 number,
651 keyword,310 string,31 regexp,40 operator and3 syntax characters. These are
character counts across variants, not numbers of problems. Repeated missing whole
keywords include `else` in25 programs, `break` in20 and `continue` in18. Strict mode
also lacks closing-delimiter seams: unsupported `}` occurs in223 programs. Those
gaps explain why another search over the same pool cannot repair all coverage.

## The newer token-join pool

The [pool-only audit](development-replay-v1/token-join-pool-diagnostic.json) preserves
the concurrent upstream lexer-window and padded-character-exclusion changes.
Under the same pinned Mac parser/input
scope, strict combined-pool reachability rises from0 to195/250; punctuation-fallback
reachability rises from127 to201/250. This audit performs no dictionary fit and
must not be attributed to a selected profile or to a different runtime's run.

The remaining fallback49 comprise47 candidate-scarcity and2 boundary-only cases.
Unsupported character counts are159 identifier,339 number,20 keyword,306 string,
31 regexp and6 operator characters. For the201 representable problems, a necessary
shared-entry lower bound is72 and one complete-path union uses2559 entries. Thus a
shared256-entry solution is neither demonstrated nor excluded. All201 have an
individual minimum-path witness within256; their union is not a256-entry witness.

Both audits were bounded to180 seconds with a2GiB sampled process-group RSS guard.
The retained audit completed in8.16 seconds, sampled peak344915968 bytes; the
current-pool audit took8.17 seconds, sampled peak341164032 bytes. No hard aggregate
memory limit or between-poll peak guarantee is claimed.

## Concrete next work

The token-join fix already addresses the dominant old syntax gaps; do not repeat
that work or run another blind sweep. Use the remaining hashed spans and complete
path bundles to isolate a small, declared shared-capacity subproblem. Preserve
the existing lexical/singleton rules and retain failed coverage. Do not substitute
an individual witness or an unlimited pool for a legal shared dictionary.

Descriptive, overlapping source cohorts include indexed loops148, while loops94,
for-of loops92, push/pop calls79, map/set construction46, sorting calls25, tree-link
syntax11 and list-link syntax8. These are syntactic observations, not semantic
families or new split/group authority. They identify places to look for already
qualified consistent loop, traversal, counter and container alternatives. Preserve
input mutation/aliasing, numeric behavior and asymptotic work; charge every helper
and adapter. No new rewrite is admitted by these observations.

The available trusted receipt bundle has265 qualified JS records for these250
IDs but no different source hash. The separate166-alternative historical result
requires its authentic `fit-pool.json` and sibling run `contract.json`: exact
`qualification_report_sha256`, `qualification_contract_sha256`, per-alternative
`adapted_sha256`, candidate/semantics/adapter hashes and complete byte counts.
`paired-authoring-v1/verify_adapted.py` owns that evidence. Missing metadata is not
proof that no alternatives exist. Exact source/contract/effect/complexity scope and
fit membership must join before representability comparisons can reuse them.

For Python, `python-literals-v1/prepare.py` writes the private
`gamma.python.systematic-literals.v1` contract with `source_rows`, `owners`,
`references`, `families` and `proofs`. Its input freeze is another `contract.json`,
schema `gamma.python.adapted-sources.v1`, with each source/semantics hash, method
and original-source hash. The private trace identifies262 of the historical272
IDs carrying a common current-receipt freeze anchor;229 remain after known group
exclusions if the missing report-to-run-contract freeze link verifies. These are
conditional joins, not fitting admission. Recover the authentic metadata where
the evidence already resides; do not manufacture hashes or require a new optional
ledger retroactively. Qualification execution remains assigned to dot.

The counted fragment/spelling extension is a separate representation with its own
mode/byte/control costs. This pure-literal diagnostic neither evaluates nor
qualifies it. No protected payload, private archive transfer, source execution,
profile promotion, browser admission or deployment occurred here.
