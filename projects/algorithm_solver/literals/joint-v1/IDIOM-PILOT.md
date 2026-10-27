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

## Pinned input contract

The larger-corpus fitting CLI requires an
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

The current admission projection defaults to unknown memberships/unreviewed
closure. It therefore cannot be fitted until authentic exposure, grouping,
variant and policy joins exist. This tool does not assign those joins, qualify
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

Focused checks (set `GAMMA_TEST_NODE` to an existing Node path to include its
parse-only integration check):

```sh
GAMMA_TEST_NODE=/absolute/existing/node python3 -m unittest discover \
  -s projects/algorithm_solver/literals/joint-v1 -v
```

## Historical control and retained failures

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
