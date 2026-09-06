# MIDAS boundary observer

`tools/midas_open_boundary_observer_v1.py` builds an observation-only successor
around the unchanged standalone MIDAS codec. It records every pre-truth Q16
probability and serialized state at initialization, every 32 decoded bytes, and
finalization. The archive framing and predictor/update law remain v1.

Each fresh encode/decode process publishes one new directory atomically, after
closing its six files: `data`, `state.bin`, `summary.json`, `probabilities.bin`,
`boundaries.jsonl`, and `snapshots.bin`. Existing output paths are refused.
The decoder receives its archive and independently derives all predictive state.

Boundary records hash the complete serialization and 16 named component ranges,
including parameters, optimizer moments and compensation, recurrent memory,
incremental cache, scheduler, byte prefix, parent/reference projections, and
normalized arithmetic coder state. Exact boundary snapshots are available for
fixtures of at most 129 raw bytes. Larger inputs retain streamed probabilities
and state hashes; they do not retain full state at every boundary.

Run from `projects/enwiki9/` using an existing compiler and assigned resources:

```bash
python3 tools/midas_open_boundary_observer_v1.py encode \
  --cache-dir results/NEW_UNIT/cache --arm P --max-raw-bytes 65 \
  --wall-seconds 120 --input SYNTHETIC_INPUT \
  --output-dir results/NEW_UNIT/P-encode --snapshots
python3 tools/midas_open_boundary_observer_v1.py decode \
  --cache-dir results/NEW_UNIT/cache --arm P --max-raw-bytes 65 \
  --wall-seconds 120 --input results/NEW_UNIT/P-encode/data \
  --output-dir results/NEW_UNIT/P-decode --snapshots
python3 tools/midas_open_boundary_observer_v1.py compare \
  --reference results/NEW_UNIT/P-encode --target results/NEW_UNIT/P-decode \
  --diagnostic results/NEW_UNIT/comparison.json
```

Use `--projection parent` for P/K comparisons: complete scheduler states differ
because K retains discarded bookkeeping. Same-arm encode/decode/repeat
comparisons use the default complete projection. A passing comparison validates
both complete bundles; identical malformed traces cannot pass. Divergence
diagnostics retain neighboring probabilities or boundary records and identify
the first differing component. Hashes do not reconstruct missing state bytes.

Native limits remain 250,000 raw bytes, 512 MiB address space, 120 CPU seconds,
and 32 MiB per file; the wrapper requires an explicit wall stop at most 120
seconds. The build cache separately bounds the compiler. Aggregate CPU, memory,
scratch and elapsed admission belong to the enclosing test or frozen gate.
Build/runtime closure and complete submission packaging remain separate duties.

The synthetic regression suite is
`python3 -m unittest discover -s tests -p test_midas_open_boundary_observer.py -v`.
Set `MIDAS_OBSERVER_UNIT_DIR` to a new output directory to retain its build and
fixtures. Corpus execution requires a separately frozen, published candidate;
fixture correctness alone cannot promote the existing corpus result.
