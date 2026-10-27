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
Single-character whitespace remains charged and is reported separately.

## Pinned input contract

The fitting CLI no longer loads the fixed scale80 population. It requires an
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
- Reject duplicate variants/bytes. Request source only through the existing
  service, which repeats its live boundary before opening. Recheck exact bytes.

The current admission projection defaults to unknown memberships/unreviewed
closure. It therefore cannot be fitted until authentic exposure, grouping,
variant and policy joins exist. This tool does not assign those joins, qualify
new variants, establish licenses, admit browser guides or grant publication.
The bounded loader accepts up to 4096 selected variants per language and 32 MiB
of source text; this is capacity, not a claim that a population is eligible.
Mining also caps distinct proposals at 250000 and spans at 512 per source.
Exceeding a bound fails explicitly; it does not silently sample or regroup.

```sh
python3 projects/algorithm_solver/literals/joint-v1/idiom_pilot.py \
  --config /absolute/private/fitting-config.json --config-sha256 EXPECTED_SHA256 \
  --objective singleton \
  --output /absolute/private/new-run
```

For JavaScript also supply `--node /absolute/pinned/node --node-sha256 SHA256`.
Python records its actual runtime version and executable hash. Outputs bind all
metadata/code/runtime pins, exact memberships and source hashes. Output contains
reconstructable development text and must remain in the authorized private
location; the repository contains tooling and synthetic tests only.

## Accounting and acceptance

The evaluator's historical default still includes its 96-entry alphabet.
Explicit `alphabet=[]` enables charged 4–8-bit experiments without that floor.
Unrepresentable text never skips a gap: its longest reachable prefix and minimum
path are retained, and the entire remaining suffix is uncovered. Only complete
sources count toward coverage, selections or percentiles. Equal-cost paths use
lower dictionary IDs; source ties use UTF-8 byte length then stable variant ID.
Cache reuse binds source bytes and shared literal order. The historical
`search.py` scale80 CLI remains available for reproducing its old experiments.

The default `singleton` objective orders complete coverage first, then absolute
singleton bits, total literal bits and dictionary-plus-packet storage. It never
optimizes a singleton percentage: adding selections to inflate its denominator
cannot improve the objective. `input` and `storage` objectives remain explicit
alternatives. The Pareto dimensions retain coverage, absolute singleton bits,
total literal bits and full package bytes, exposing tradeoffs rather than
concealing a larger total cost behind a lower singleton share.

All four pools share each width's entry budget and search bounds. Reports retain
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
