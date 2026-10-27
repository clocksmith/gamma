# Exact idiom development fitting

`idiom_pilot.py` reuses this directory's joint source/dictionary evaluator. It
compares language-specific assistant-authored concrete strings, exact syntactic
spans, their union, and a separate arbitrary-substring compression control.
Python uses its AST; JavaScript uses the explicitly pinned Node runtime's Acorn.
Parsing never imports or executes a candidate. Expressions, statements and
contiguous two/three-statement spans retain original names, operands, whitespace
and punctuation, up to 160 UTF-8 bytes. Whole source programs, complete function
units/bodies (including whitespace-disguised copies), and whitespace-only
multicharacter entries are excluded. Every candidate must occur in at least two
distinct canonical problems; multiple variants do not count as reuse. Occurrence
ranking uses nonoverlapping counts, maximized across variants per problem.
Human-oriented pools require lexical-boundary reuse across problems and enforce
those boundaries in each exact segmentation. Strict arms forbid all singleton
entries. Fallback arms permit only charged punctuation, operators and whitespace,
never letters or digits. Complementary source-path bundles seed the dictionary;
no alphabet receives slots first. The strict initializer also competes in the
fallback arm. Empty pools remain explicit zero-coverage, unserializable states.

## Historical exposed development replay

An existing fit contract is sufficient authority for its exact source bytes;
optional modern authoring records are not a retroactive requirement. The
`gamma.idiom-development-replay-config.v1` route has exactly `schema`, `language`
(`javascript`), `service`, `source_contract` and `qualification_contract`. The last
three are absolute path/SHA256 descriptors. It consumes the existing
cost-decomposition source contract and name-search qualification contract, checks
their parent hash, identical complete fit/validation partition, exact numeric
aliases and source/case commitments, and joins current qualified canonical bytes.
Changed sources and Python cannot inherit this JavaScript exact-source grant.

`guide_admission.reconcile_development_replay` owns this metadata join. It preserves
canonical variant IDs and current receipt problem-contract/semantics bindings;
no new variant registry, sidecar hash, qualification or split is invented. Both
language slots share canonical problem grouping. Existing corpus-key aliases and
the recognition owner's roman-suffix sibling rule identify known group conflicts;
fit members linked to validation, reserved or unknown/outside members are excluded
without reallocation. Missing full near-duplicate closure remains explicit.

This reruns an already exposed development fit. It creates neither a new grouped
corpus assignment nor independent confirmation, and cannot establish unseen
generalization. Unknown closure still blocks a fresh confirmation claim; it does
not retroactively revoke the historical exact-source fitting authority. The full
historical denominator and per-record exclusions remain in the private contract.
All source opens still use the live existing service boundary and exact hashes.

## Modern authoring input contract

The modern larger-corpus route requires an
absolute hash-pinned `gamma.idiom-fitting-config.v1` JSON file with exactly these
fields: `schema`, `language` (`python` or `javascript`), `service`, `admission`,
`authoring_catalog`, and `fitting_policy`. Each of the last four fields is an
existing service-style descriptor `{ "path": "/absolute/path", "sha256": "..." }`.
The service and its existing receipts, canonical metadata and source boundary
remain authoritative. Admission is the existing
`gamma.source-to-guide-inventory.v1`; authoring variants use the existing
`algsolve/authoring_variants.py` owner and its unchanged stable identities.
Authoring provenance paths are never followed.

The externally reviewed fitting policy has exactly `schema`
(`gamma.idiom-fitting-policy.v1`), nonempty `authority` and `reference`, `purpose`
(`development-fitting`), `inputs`, and `variants`. Its `inputs` binds the exact
`service_sha256`, `admission_sha256` and `authoring_catalog_sha256`. Each selected
variant has exactly integer `problem_id`, `language`, `variant_id`, `membership`
(`development_fit`), and `group_id`. These are trusted operator inputs requiring
actual reviewed records; writing a policy or hash does not create permission.

All selected metadata is preflighted before the first source request:

- Preserve the complete admission denominator and exact service binding.
- Require the live boundary's exact source permission binding, already-exposed
  status and explicit existing `development_fit` membership.
- Require reviewed near-duplicate closure, a preserved group ID and languages
  kept together. Reject groups crossing heldout, unknown or closed membership.
- Recompute the existing authoring identity without changing its unknown
  qualification status. Require its exact source/contract to join a currently
  qualified canonical slot and the admission row's six bindings and receipt.
  Source availability alone never establishes qualification.
- Require completed development admission, no outstanding blockers, and joined
  license/adapter records. A qualification receipt alone is insufficient.
- Reject duplicate variants/bytes. Request source only through the existing
  service, which repeats its live boundary before opening. Recheck exact bytes.

The current prospective admission projection defaults to unknown memberships/
unreviewed closure. This route therefore needs authentic exposure, grouping,
variant and policy joins. Existing historical replay uses the route above rather
than treating optional new records as a retroactive gate. This tool assigns no joins, qualifies
new variants, establish licenses, admit browser guides or grant publication.
The bounded loader accepts up to 4096 selected variants per language and 32 MiB
of source text; this is capacity, not a claim that a population is eligible.
Mining also caps distinct proposals at 250000 and spans at 2048 per source.
Exceeding a bound fails explicitly; it does not silently sample or regroup.

```sh
python3 projects/algorithm_solver/literals/joint-v1/idiom_pilot.py \
  --config /absolute/private/fitting-config.json --config-sha256 EXPECTED_SHA256 \
  --objective compact \
  --output /absolute/private/new-run
```

For JavaScript also supply `--node /absolute/pinned/node --node-sha256 SHA256`.
Python records its actual runtime version and executable hash. Outputs bind all
metadata/code/runtime pins, exact memberships and source hashes. Output contains
reconstructable development text and must remain in the authorized private
location; only aggregate measurements and already-public historical controls are retained in Git.

## Accounting and acceptance

The evaluator's historical default still includes its 96-entry alphabet.
Explicit `alphabet=[]` enables charged 4–8-bit experiments without that floor.
Unrepresentable text never skips a gap: its longest reachable prefix and minimum
path are retained, and the entire remaining suffix is uncovered. Only complete
sources count toward coverage, selections or percentiles. Equal-cost paths use
lower dictionary IDs; source ties use UTF-8 byte length then stable variant ID.
Cache reuse binds source bytes, lexical boundaries and shared literal order. The historical
`search.py` scale80 CLI remains available for reproducing its old experiments.

The default `compact` objective prefers dictionaries meeting the aggregate
10% singleton, median 32 and p95 96 constraints before comparing compliant
program counts, coverage, reachable prefixes and costs. Every denominator stays
fixed; incomplete sources and constraint failures remain in the report. Prefix
progress is a search signal, never complete coverage. Qualified source
alternatives compete on those limits while each retains its minimum path.
No padding is permitted. The `singleton` control orders coverage, absolute
singleton bits, literal bits and storage; `input` and `storage` remain explicit
controls. Pareto dimensions use absolute singleton bits, never a ratio that
can reward a larger denominator. Selections and encoded bits are not measured
interaction presses or human effort.

Both arms of all four pools share each width's entry budget and search bounds. Reports retain
coverage/denominator at each width, absolute singleton bits and selections,
p50/p95, dictionary bytes, packet headers, payload padding, complete packet and
package bytes, source UTF-8 size, whitespace use, exact paths, and per-problem
regressions. Selected codec source sizes are reported separately from complete
installed runtime footprint. Helpers and operands receive no free expansion.
No editor-control cost, human fluency or readability score is inferred.

Historical scale80 pilot findings remain unchanged and unsuccessful. Larger
synthetic fixtures test plumbing and accounting, not real problem coverage.
Repeated exposure cannot supply independent confirmation. No result changes the
original population, coverage, median 32, p95 96 or 10% singleton-bit gates.
`pilot_numeric_thresholds_met` describes only the supplied development population;
`original_population_gate_evaluated` and `milestone_qualified` remain false.
No fitted profile is promoted or deployed.

## Historical development replay result

The [pre-integration character-floor comparator](development-replay-v1/summary.json)
retains its original code pins and measured implementation identity. It predates
the upstream strict/punctuation lexical policy integrated below; its full-coverage
results are not results under that newer policy. It uses 250 exposed,
byte-identical JavaScript fit sources from the historical 300/100 split. Of 287
matching fit sources, 37 are excluded by known cross-membership alias/sibling
groups; 13 other current canonical fit sources differ from the historical bytes.
The 100 validation members remain excluded. No optional authoring ledger is
required retroactively, and this JavaScript authority is not transferred to Python.

One matched round per pool/width completed in 32.71 seconds. The final run's
sampled peak process-group RSS was 317816832 bytes, below its 2 GiB sampled guard;
the wall limit was 180 seconds. This is sampled monitoring, not an OS memory-limit
or between-poll peak claim. Initial/final packets passed 5544 canonical round trips.
The report preserves prior attempts and all 20 arms; no source strings, dictionary
entries, literal-ID sequences or private membership lists are published.

Best final arm at each width, ordered by coverage then absolute singleton bits,
total literal bits and package bytes:

| Width | Pool | Coverage | Selections | Singleton bits | Median / p95 | Package bytes |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | seed | 0/250 | 0 | 0 | unavailable | 83 |
| 5 | seed | 0/250 | 0 | 0 | unavailable | 163 |
| 6 | seed | 193/250 | 41168 | 247008 | 193 / 432 | 39189 |
| 7 | seed | 250/250 | 38801 | 224210 | 126 / 323 | 45160 |
| 8 | seed + AST | 250/250 | 32219 | 203400 | 99.5 / 301 | 45660 |

At width 8, seed-only uses 38116 selections, 249496 singleton bits and 49408
package bytes. The combined arm improves those costs but still has 78.91%
singleton bits. Machine-only spans are worse than seeds at both full-coverage
widths. No arm passes the unchanged 32/96/10% gates; the original frozen-population
gate is not evaluated. Low-width zero/partial coverage is failure, not cheap
complete representation. This limited search is not an infeasibility result.

The [integrated constrained comparison](development-replay-v1/constrained-summary.json)
preserves both upstream singleton arms and complete lexical boundaries on the
same 250 sources. All 40 matched arms completed in 85.92 seconds, sampled peak
process-group RSS 318324736 bytes, with 526 initial/final canonical packet round
trips. Strict human-oriented pools cover **0/250 at every width**. Highest human
pool coverage with punctuation-only fallback is:

| Width | Pool | Coverage | Selections | Singleton bits | Median / p95 | Package bytes |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | AST | 3/250 | 19 | 20 | 5 / 9 | 544 |
| 5 | seed + AST | 6/250 | 45 | 60 | 8 / 10 | 889 |
| 6 | seed + AST | 12/250 | 140 | 276 | 10.5 / 31 | 1607 |
| 7 | seed + AST | 23/250 | 297 | 539 | 13 / 19 | 2949 |
| 8 | seed + AST | 43/250 | 694 | 1296 | 16 / 23 | 5770 |

These percentiles describe covered programs only. Every arm fails supplied-
population qualification; the denominator remains 250, with exclusions against
the historical 400 also retained. Compression-only fragments remain a separate
unrestricted-boundary control. This is a measured coverage bottleneck under the
bounded proposal/initializer policy, not evidence that larger vocabularies or
all equivalent programs are impossible. The candidate pools contain 57 seeds,
3686 syntactic spans, 3716 union entries and 29465 compression fragments.

Focused checks (set `GAMMA_TEST_NODE` to an existing Node path to include its
parse-only integration check):

```sh
GAMMA_TEST_NODE=/absolute/existing/node python3 -m unittest discover \
  -s projects/algorithm_solver/literals/joint-v1 -v
```

## Historical control and retained failures

### Complete-token joins, 250-source replay

The [token-join replay](development-replay-v1/token-joins-summary.json) retains
the same 250 exact, previously exposed JavaScript fitting sources. Machine
proposals now include windows of one through three complete lexer tokens, with
their exact intervening/trailing whitespace. These fill gaps between AST nodes;
they do not rewrite sources or substitute parameters. Human-oriented pools also
reject whitespace-padded single characters. All existing reuse, token-boundary,
complete-answer exclusion and exact-decoding checks remain in force.

The combined strict arm produced these fitted results:

| Entries | Complete programs | Median / p95 selections | Singleton bits |
| --- | --- | --- | --- |
| 64 | 11/250 | 7 / 11 | 0 |
| 128 | 21/250 | 10 / 15 | 0 |
| 256 | 38/250 | 12 / 17 | 0 |

Percentiles describe covered programs only; all uncovered programs remain in the
250 denominator. The preceding strict replay covered zero at each width. Its
restricted-fallback 256-entry result covered 43 but used 23.34% singleton bits;
the new result is a tradeoff, not a claim of higher coverage than that result.
All supplied-population and original milestone claims remain false.

Forty bounded comparisons completed with 882 successful initial/final packet
round trips. Search elapsed time was 56.91 seconds; the entire systemd unit ran
62.63 seconds with a 214.3M reported peak under a 2 GiB memory limit and 360-second
runtime limit. The report binds code, inputs and private full traces.

A separate development probe weighted seed paths by cross-problem reuse before
evaluating their genuine minimum-cost encodings. Its best 256-entry candidate
covered 41/250 with median 16, p95 30 and zero singleton bits. Stronger reuse
weights increased selection costs without improving coverage. This probe is
retained separately, not installed as the optimizer default. Neither run creates
source qualification, Python fitting authority, browser admission, publication,
fresh confirmation or evidence of human usability.

An explicit `--legacy-scale80-control` flag reproduces only the hash-pinned,
already-exposed 80-problem control. It is mutually exclusive with `--config` and
does not admit a larger corpus or confer fresh evaluation status. The control
keeps its historical finite evidence and unresolved modern variant joins.

`idiom-results-20261027.json` retains aggregate failed comparisons, binding each
attempt to its actual code and inputs. Earlier attempts predate the integration
of larger spans and complete-function exclusions; do not attribute them to a
later implementation. The integrated replay is recorded separately. None of
these results qualifies the original compact-library milestone or establishes
human usability. No vocabulary was deployed from these runs.
