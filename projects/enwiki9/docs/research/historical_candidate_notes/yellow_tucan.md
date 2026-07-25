# yellow_tucan Notes

Date: 2026-05-09

## What Changed

Added and smoked a no-cmix, no-lzma custom compression line:

- `yellow_tucan_range_order_v1`: byte arithmetic coder with adaptive order contexts.
- `yellow_tucan_structural_range_v1`: arithmetic coder where MediaWiki parser state selects probability tables.
- `yellow_tucan_structural_range_v2`: adds trained-context fallback so sparse structural states do not replace useful lower-order models.
- `yellow_tucan_structural_range_v3`: tests integer mixture of global, previous-byte, and structural distributions.
- `yellow_tucan_structural_range_v4`: tests a larger structural context table.
- `yellow_tucan_structural_range_v5`: same archive behavior as v2 with smaller counted source.

All new `yellow_tucan_structural_range_*` programs are dependency-free Python. Decoder inputs are only `program.py` plus the archive returned by `compress()`.

## Measured Results

Custom range-coder results:

| program | scope | compressed_size | program_size | S | b/B | roundtrip | determinism |
|---|---:|---:|---:|---:|---:|---|---|
| `yellow_tucan_range_order_v1` | 1 MB | 460,812 | 6,202 | 467,014 | 3.686496 | true | true |
| `yellow_tucan_structural_range_v2` | 1 MB | 455,242 | 7,089 | 462,331 | 3.641936 | true | true |
| `yellow_tucan_structural_range_v3` | 1 MB | 468,478 | 6,633 | 475,111 | 3.747824 | true | true |
| `yellow_tucan_structural_range_v4` | 1 MB | 455,242 | 7,142 | 462,384 | 3.641936 | true | true |
| `yellow_tucan_structural_range_v5` | 1 MB | 455,242 | 6,793 | 462,035 | 3.641936 | true | true |

Best custom no-cmix/no-lzma result so far:

`yellow_tucan_structural_range_v5` at 1 MB:

- `compressed_size = 455,242`
- `program_size = 6,793`
- `S = 462,035`
- `b/B = 3.641936`
- `roundtrip_ok = true`
- `single_host_byte_equal = true`

Structural context is a real signal: v5 beats the plain order model at 1 MB by 5,570 archive bytes and 4,979 score bytes. That is the useful part of the new architecture.

The integer mixture in v3 is not ready. It wins on smaller prefixes, but loses at 1 MB. Treat it as evidence that mixture weights need an admission rule, not as the current path.

The larger context budget in v4 does not help at 1 MB. It matches v2 archive bytes and loses on program size.

## Current Best No-Cmix Practical Line

The LZMA-backed opcode programs still dominate measured no-cmix score:

- `yellow_tucan_markup_opcode_lzma2_1g_v1` at 100 MB: `S = 24,665,245`, `b/B = 1.97314`.
- `ast_opcode_lzma_v1` at full 1 GB: `S = 196,775,973`, `b/B = 1.574189`.

Those are not the new architecture; they are markup substitution plus a strong LZMA-class backend. They remain the best measured no-cmix path in the repo.

## Theory Update

The best non-cmix architecture should not rewrite the byte stream first. The evidence points to:

Raw bytes -> deterministic parser state -> adaptive predictor -> arithmetic/range coder.

That preserves the exact byte stream while letting the model learn that `<text>`, links, entities, digits, braces, and brackets imply different byte distributions. This is closer to language-aware compression than string substitution, but it still needs a stronger predictor before it can challenge LZMA.

## Next Steps

1. Build `yellow_tucan_structural_range_v6`: keep v5's selected-context discipline, but add PPM-style escape/backoff so structural context, previous-byte context, and global context contribute without the blunt v3 mixture.
2. Add parser-state refinements that cost no archive bits: tag-name state, entity state, link-target state, template-key state, numeric-run state, and prose-vs-markup state.
3. Replace repeated cumulative scans with a compact cumulative table or Fenwick tree only if richer models make the current coder the bottleneck.
4. Add a measured ablation table for each new feature at 100 KB and 1 MB before promoting it.
5. Promotion gate for the custom architecture: beat `yellow_tucan_structural_range_v5` at 1 MB first, then beat `yellow_tucan_markup_opcode_lzma_v2` at matching scope. Until then, do not claim a 10 percent path.

## Retired Or Parked

- `yellow_tucan_structural_range_v3`: parked; mixture weights are too blunt at 1 MB.
- `yellow_tucan_structural_range_v4`: parked; larger context budget did not improve archive bytes.
- Fixed-span macro mining remains retired unless a same-scope ablation shows net archive gain.
