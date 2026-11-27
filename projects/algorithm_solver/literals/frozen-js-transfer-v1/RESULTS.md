# Fixed-vocabulary headers and depth-one frames on fresh JavaScript

The independent cohort author selected 20 small JavaScript repositories from distinct owners. All 77 tracked regular JavaScript files entered the comparisons, totaling 123,315 original bytes. The [sampling protocol](COHORT.md) describes the repository-size window, immutable Git pins and exclusion coverage. Both scorers used [the same manifest](source_manifest.json).

| Sealed comparison | Baseline | Candidate | Decision |
| --- | ---: | ---: | --- |
| A1a pooled complete bytes, large matched DAG-header budget | Open 111,112 | Exact-closed 103,799 | Exact-closed saved 7,313 bytes |
| A1a pooled minimum-DP tokens, same budget | Open 60,000 | Exact-closed 46,427 | Exact-closed saved 13,573 tokens |
| A2 complete bytes, header paid once | Context AST 47,776 | Depth-one frames 48,700 | KILL at the frozen 1% saving bar |

**A1a.** Both primary measures improved in each of the 20 repositories (two-sided paired sign test, (p=0.00000191) for each). Changing only the header to the construction DAG reduced complete bytes and preserved payload and reconstruction in every tested cell. Both stock HF and pinned tiktoken passed the applicable parity checks. The large-budget BPE arm used 102,415 complete bytes. Pair-byte used 45,072 minimum-DP tokens. Lean zstd-19 with an 8 KiB dictionary used 48,009 bytes. Its C decoder took 8.475 microseconds at p95 versus 11,615 microseconds for the exact-closed Python reference decoder. Random-access sizes use record-padding and framing accounting. The sequential streams were independently decoded. [Full A1a receipt](result_a1a.json)

**A2.** Frame definitions and code tables added 1,059 header bytes. They saved 135 payload bytes on this cohort. The net increase was 924 bytes (1.934%, paired repository bootstrap 95% interval +1.4054% to +2.8393%). Both archives reconstructed every target. The six raw fallbacks represented 16.31% of normalized or fallback bytes. Decode p95 was 18.32 ms for context AST and 23.26 ms for frames. The frozen scorer uses text-mode input, so an independent byte check also compared each decoded fallback with the original Git blob. It detected a deliberately malformed CRLF development fixture and recorded zero discrepancies on this cohort. [A2 score](result_a2.json) · [Independent fidelity check](a2_raw_fidelity.json)

## Reproduce

Materialize and verify the pinned inputs following [COHORT.md](COHORT.md). From this directory use a Python environment containing NumPy, Hugging Face tokenizers, SentencePiece and `tiktoken==0.14.0`, with Node and libzstd available. Keep outputs outside the repository.

```sh
python a1a_fit.py /tmp/a1a-primary-tables.json
python score_a1a.py --tables /tmp/a1a-primary-tables.json --manifest source_manifest.json --root /tmp/bits-frozen-js-v1/corpus --output /tmp/a1a-score.json
python run_a2.py source_manifest.json /tmp/bits-frozen-js-v1/corpus /tmp/a2-score
```
