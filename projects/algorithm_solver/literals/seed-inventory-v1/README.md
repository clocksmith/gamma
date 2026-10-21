# Source-witness inventory v1

Standard-library CPU preprocessing for the existing Jupiter optimizer, not a new optimizer or candidate runner. Reads only explicitly supplied delivery manifests and their hash-pinned source inventory. No candidate import, evaluation, judge execution, network or GPU use.

## Reproduce

From this directory, with the three preserved assignment directories as siblings:

    python3 -m unittest -v
    python3 inventory.py ../assigned-v1/DELIVERY_MANIFEST.json ../assigned-v2/DELIVERY_MANIFEST.json ../assigned-v3/DELIVERY_MANIFEST.json --output witnesses.json

The output is deterministic for the same input bytes and directory labels, independent of argument order and absolute workspace location. Output intentionally contains manifest and source SHA-256 values, but no private test bodies or private ledger data. A changed manifest changes provenance even if extracted literals are unchanged. Inputs are supplied authority, not independently re-cleared by this tool.

## Exact matching and integration

1. Verify delivery manifest/source hashes using the normal coordinator gates. This script also refuses source hash mismatch, duplicate language/problem identities, root escape and unsupported source extensions.
2. Consume witnesses.json grouped by language plus literal. Each record has exact text, UTF-8 text hash, source/1-based line occurrences, occurrence count and distinct problem count. Only records witnessed in at least two distinct problem IDs are emitted. Language spaces are separate.
3. Matching normalizes LF/CRLF/CR terminators only and excludes them. All leading/trailing horizontal whitespace remains literal. Blank lines are omitted. A final newline does not create an occurrence. UTF-8 must decode strictly.
4. These are COMPLETE PHYSICAL LINES, not a JavaScript/Python parser's complete statements. Braces, headers, comments and multiline fragments can appear. Do not ingest automatically as executable vocabulary. Let the existing AST/frontend identify valid complete statements and bindings; retain physical-line witnesses as provenance.
5. annotations.json provides human-curated contracts, observed examples and explicitly proposed alternatives. Its display strings omit indentation; this is not the inventory matching policy. Do not equate identical text with semantic interchangeability or alpha-renamed text with literal reuse.
6. Preserve binding scope, key equality/type, mutation/aliasing, integer bounds and complexity. Rewrites require new source hashes, review and unchanged isolated tests. Source 1762/1885 exposure labels remain applicable.

Results: 120 sources, 60 distinct problem IDs, 187 cross-problem language-specific physical-line witnesses. No compression benefit, optimality, runtime correctness or campaign admission is asserted.

No existing source, ledger, assignment artifact or repository optimizer file is edited. Local test fixtures are synthetic strings exercising the inventory, not private algorithm tests.
