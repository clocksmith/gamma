# Bounded compact substring search

Owner: [Algorithm Solver charter](../../CATSCAN.md). This fixed-source development
experiment is **negative**, not M1 qualification. It executes no candidate source.
[Predeclared policy](FREEZE.md) and [aggregate results](results-summary.json) retain
the exact scope, budgets and evidence identities; private source/dictionary/packet
artifacts remain outside the repository.

All four searched dictionaries were sealed before opening the 100 already-consumed
development-validation sources. The 300 fit sources alone supplied proposals and
search scores. Six dictionaries (two pinned controls plus four search arms) produce
2,400 exactly verified packets across fit/validation. Full source, helper, framing,
dictionary, padding and decoder costs remain counted. No final 100 or protected 66
payload was opened, and no fresh behavioral qualification follows from decoding.

## Development-validation results

| Capacity / arm | Selections | Median | p95 | Character bits | Package + decoder bytes |
|---|---:|---:|---:|---:|---:|
| 128 pinned L-R | 14,014 | 103.5 | 320 | 78.671% | 25,465 |
| 128 selection search | 14,006 | 103.5 | 322 | 78.623% | 25,456 |
| 128 character-budget | 14,014 | 103.5 | 320 | 78.671% | 25,465 |
| 256 pinned L-R | 8,948 | 63.5 | 211 | 55.141% | 23,495 |
| 256 selection search | 8,948 | 63.5 | 211 | 55.141% | 23,495 |
| 256 character-budget | 8,948 | 63.5 | 211 | 55.141% | 23,495 |

Zero whole-source/solve-body entries were observed in all profiles. The 128-entry
selection arm saves eight validation selections but worsens its tail. Neither
character-budget arm accepts a move. Every arm remains well outside M1's median 32,
p95 96 and character-bit 10% gates. This is a matched pinned L-R reproduction, not
an asserted reproduction of later unavailable stronger dictionaries.

The fit-only proposal rank retained 2,048 of 223,244 eligible repeated substrings,
excluding 221,196. Search ends at no improving *proposed* neighbor, not a global
optimum or evidence that search headroom is exhausted. In particular the saving-
ranked pool can omit useful character-focused candidates. All four searches used
identical declared neighborhood/evaluation policies and stayed under their CPU cap.

Two earlier attempts failed closed before fitting on unsupported declaration or
simple-template shapes; they remain retained outside the repository. The final
frozen lexer accounts for complete named solve bodies among fully charged helpers,
quoted strings, comments, expression-position regexes and simple identifier-
interpolation templates. Complex templates and ambiguous declarations fail closed.

## Verification and reproduction

Seven synthetic unit tests cover distinct-program support, complete-body exclusion,
opaque brace handling, canonical exact paths, unaffected-program cache equivalence,
full-rescore search equivalence and independently decoded full-cost packets.

```
python3 -B -m unittest -v test_search
python3 -B search.py freeze --root PRIVATE_IMPORT --output NEW_FREEZE
python3 -B search.py run --root PRIVATE_IMPORT --freeze NEW_FREEZE --output NEW_RUN
```

Use fresh output directories outside the repository and an outer process-group
wall/memory limit. The recorded run used a 600-second timeout, 2 GiB address-space
limit, 540 CPU seconds and 32 process limit; it exited successfully and its owned
search process was absent after completion. The frozen per-arm 120 CPU-second cap
is independent of the outer safety envelope. The private import must pass the
existing exact transfer receipt, allowlist, partition and payload-hash checks.
