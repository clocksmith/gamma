# Freeze progress: PAUSED, nothing is pinned

**This is not a freeze.** The work was paused by the owner on 2026-11-25 at 15:30:06 UTC, before any of
the six items in `PREREGISTRATION.md` was pinned. There is no `FREEZE.json`. The test sets must stay
sealed. Every number below is a measurement on training and validation records, and every choice is
provisional.

Times are from `date -u`: started 13:38:07Z; machine hold 13:46 to 14:20, during which nothing was run;
all jobs stopped 15:30:06Z.

## What the freeze owner read

- Read: this repository; the training and validation records of the three workloads; the reference
  FSST sources (checkout at `e638d4cf8c26129d73c242a4127b42b975de5b63`, confirmed with
  `git rev-parse HEAD`); the exported records of the lane's old suites.
- Not read, listed or searched: the test records, the test source list, the split salt, the sealed
  archive, the custodian's keys or working files, any other session's files. No network was used.

Hashes of what was read (SHA-256):

| File | SHA-256 |
|---|---|
| `short-record-decision-v1/PREREGISTRATION.md` | `b85744b11a963f19a4f9c0b371d4a3abd64ed0d6f69a79ff40f57fc6d334f870` |
| `fresh-short-records-v1/manifest.json` | `8bf91fb57ded59473bedd7f2a39a1ac86e55336d7a2e9baa6882cfb2fdfc00d4` |
| `codenet-replication-v1/byte_encode.py` | `2f03a09e0fe55af0cfe25bad607df0d27b21df6b021d2d2f0d08a90e34aa71cb` |
| `fixed-source-v3/engine.c` | `7331f1eb6d7866c6b71fbb0c19be6b1f8afdfa6ff9003c95604fa9051f8db19f` |
| `rung2-presearch-v1/equal_budget_eval.py` | `771f1017b1a12a00fbbbf854f7cff3bedb24571689586983a78325ac5de69bcf` |
| `rung2-presearch-v1/raw_predictor.py` | `79d74f4a748f9126418ec1a0faa7aa1cecca71682bd3345c5c14706013189d57` |
| `rung2-presearch-v1/regime_predictor.py` | `e674d3c176c64b47c27f348ff7309a68ebb8d21fd5866df5df677430b480ddbc` |
| `rung2-presearch-v1/run_completed_chain_and_regime_eval.py` | `948865c87f96c32a687573b79f657ee1ae611525e2bf9ea86f03b72f19434ddd` |
| `rung2-short-ra-bench-v1/ra_codecs_bench.c` | `14461ca79b8d27ca15af48d5089bce46ce4fea55ab554ac883242c445c592fab` |
| `rung3-archive-search-v1/indexed_archive.py` | `ca1922c10680d966cf1e7af60c76b421955ba64897a8f4520aa77a3fc84cbe02` |
| `rung3-vmm-subset-v1/transfer_vmm.py` | `1f3172af8f0e09cfe230d63ebdd18039c7eacd345859b9f4edec916d20a53028` |
| `rung3-vmm-subset-v1/vmm_subset_polish.py` | `c75ca75a623eb05a5b2323104cc1efe8d68a8c8e893bc27ae8cfa1e398dcb3d5` |
| `fair-baselines-v1/fb_candidate.py` | `5ff1d88a3cc875a89963da15c77a770d25706121763e0524f2beb4249fa16c04` |
| `fair-baselines-v1/fb_codecs.py` | `ab63cbf38d089f3921dea22fa6bf28da2a3b606a196305c46dc4903740487dad` |
| `fair-baselines-v1/fb_core.py` | `8ce3d4362de85fd9e9b8c759f9c8a0fbc2d060dda817f7f955771e815834dad2` |
| `fair-baselines-v1/fb_measure.py` | `baa22376c2659f5c992a5b23eb0907aa85f7456e96d6bb0dbf18519598c1cdc4` |
| `fair-baselines-v1/fb_native.py` | `ecc6e6a810ca1b588cf97f64ef59d716ad0d7119cea7e731123e60d0d738dde3` |
| `fair-baselines-v1/native/fb_native.c` | `abac3cfa6f259eae8ee365984eb5d1e2ca6a00cb9ce6732d5e75a0a1f1d3d977` |
| `fair-baselines-v1/native/fb_native.h` | `0b930c9fa7f369b4cbc37a50378288706975224982307ae5a84b9c6a82057a60` |
| `fair-baselines-v1/native/fb_fsst_shim.cpp` | `8c4e90fe3874f093588ba787cf0941b0ff26d1cf73d1f7e6e4f574d6bebc173a` |

The ten lane files are the ones the adapter imports or compiles. Training and validation files match
the hashes in the manifest. Libraries used: zstd 1.5.7 (static), zlib 1.2.12, Python 3.14.2. The
harness's timer advances in steps of 41 ns on the machine used.

## State of the six items

| Item | State |
|---|---|
| 1. Codec | Adapter written and checked against the lane's own scripts. Not pinned. |
| 2. Training recipe and budget | 35 configurations measured on validation. Nine queued ones not run. No choice made. |
| 3. Seed | Seeds 1, 2, 3 tried for part of the grid. No choice made. |
| 4. Baseline settings | One tuning pass done for all three workloads, with part of the grid not searched. Not pinned. |
| 5. Byte accounting | Drafted, used in all measurements below. Not confirmed through the scoring script. |
| 6. Decision rule and timing | Drafted in code only. No lookup was timed. |

## Done

### Lane configuration and entry points

- Search: `fixed-source-v3/engine.c` through `equal_budget_eval.run_engine_arm`, policy `s1-whole`,
  entry length 16, one record per file.
- Selection: `run_completed_chain_and_regime_eval.build_and_eval_bit3_pair` (MDL prefix stop, the
  recipe behind the old short-suite result) or `transfer_vmm.transfer_variational_mm` (the four cells
  of the lane's 2x2; `transfer_vmm` is the one the lane reports as best on held-out short records).
- Code tables for unseen records: minimum-token parse of the fit records, every entry without an
  occurrence counted once, canonical Huffman lengths. This is what the lane's scripts do.
- Container: `serialize_and_verify_bit3_archive` (`BIT3`). On these workloads one code table and one
  stream (layout A), because the records carry no group label that exists for unseen sources.
- Readers: the lane's Python functions, and `ra_codecs_bench.c` (`init_bit3`, `bit3_decode_one`)
  included unmodified by a C shim that exports the harness's three native functions.
- The lane's own budget rule (`regime_predictor`) returns layout A and K 4096, 2048 and 1024 for the
  three workloads' search subsets.

### Adapter

`unfinished-freeze-tools/bits_adapter.py` (class `Bit3Candidate`) with `bits_native_shim.c`.

- Fidelity check on the lane's old suites (`check_adapter_fidelity.py`, output in
  `progress-data/adapter-fidelity-old-suites.json`): the adapter through the harness, against the
  lane's own functions on the same exported records. 35 rows, difference 0 bytes in every row.

  | Suite | Configuration | Lane's script | Adapter |
  |---|---|---:|---:|
  | `short_wgsl_vs_json_80_to_80` | MDL prefix stop, lane's layout and budget rule | 12,033 | 12,033 |
  | | `transfer_vmm`, chain `bpe`, K 1024, two tables | 11,385 | 11,385 |
  | `short_ts_vs_mjs_80_to_80` | MDL prefix stop, lane's layout and budget rule | 12,397 | 12,397 |
  | | `transfer_vmm`, chain `greedy-byte`, K 1024, two tables | 12,276 | 12,276 |
  | `med_ts_vs_json_50_to_50` | MDL prefix stop, lane's layout and budget rule | 30,773 | 30,773 |

  The other 30 rows are the remaining chain and cell combinations of the two short suites. These
  suites' held-out halves were used in the codec's design; the check says something about the
  adapter only.
- On validation, all 35 configurations below reconstructed every record, decoded alone in a seeded
  random order, in both the Python reader and the C reader.

### Candidate configurations tried (validation, all-in bytes, 4 index bytes per record)

Columns: selection, search chain, budget K, records the selector and code tables saw, subset seed,
dictionary entries, single bytes added at encode time, model bytes, payload bytes, total bytes.
Sorted by total. Full rows are in `progress-data/candidate-configurations-tried.jsonl`.

`w1-short-files` (2,850 validation records, 548,025 raw bytes):

| Selection | Chain | K | Fit records | Seed | Entries | Added | Model | Payload | Total |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| transfer_vmm | greedy-byte | 4096 | search subset | 1 | 3,016 | 27 | 21,758 | 216,676 | 249,843 |
| transfer_vmm | bpe | 4096 | search subset | 1 | 2,813 | 27 | 21,197 | 220,826 | 253,432 |
| transfer_vmm | greedy-entry | 4096 | search subset | 3 | 2,726 | 22 | 23,628 | 218,750 | 253,787 |
| transfer_vmm | union_bpe_ge | 4096 | search subset | 1 | 2,953 | 27 | 25,422 | 217,509 | 254,340 |
| transfer_vmm | greedy-entry | 4096 | search subset | 1 | 2,789 | 27 | 24,326 | 219,483 | 255,218 |
| loo_only_vmm | greedy-entry | 4096 | search subset | 1 | 2,789 | 27 | 24,326 | 219,483 | 255,218 |
| transfer_vmm | greedy-entry | 4096 | search subset | 2 | 2,739 | 25 | 24,118 | 220,275 | 255,802 |
| transfer_vmm | greedy-entry | 2048 | all training | 1 | 2,008 | 10 | 16,763 | 229,818 | 257,990 |
| transfer_vmm | greedy-entry | 2048 | search subset | 1 | 1,928 | 27 | 16,222 | 230,677 | 258,308 |
| transfer_vmm | greedy-entry | 4096 | all training | 1 | 3,297 | 10 | 29,912 | 217,508 | 258,829 |
| revival_only_vmm | greedy-entry | 4096 | search subset | 1 | 3,342 | 27 | 32,103 | 219,150 | 262,662 |
| base_vmm | greedy-entry | 4096 | search subset | 1 | 3,342 | 27 | 32,103 | 219,150 | 262,662 |
| mdl_prefix_stop | greedy-entry | lane rule (4096) | search subset | 1 | 3,200 | 27 | 30,755 | 222,164 | 264,328 |
| mdl_prefix_stop | greedy-entry | 4096 | search subset | 1 | 3,200 | 27 | 30,755 | 222,164 | 264,328 |
| transfer_vmm | greedy-entry | 1024 | search subset | 1 | 1,012 | 27 | 7,541 | 247,835 | 266,785 |

`w2-message-entries` (4,950 validation records, 395,191 raw bytes):

| Selection | Chain | K | Fit records | Seed | Entries | Added | Model | Payload | Total |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| loo_only_vmm | greedy-entry | 4096 | search subset | 1 | 1,601 | 26 | 11,666 | 155,772 | 187,247 |
| transfer_vmm | union_bpe_ge | 4096 | search subset | 1 | 1,368 | 26 | 8,919 | 160,028 | 188,756 |
| transfer_vmm | greedy-entry | 4096 | search subset | 1 | 1,297 | 26 | 8,790 | 160,352 | 188,951 |
| transfer_vmm | greedy-entry | 2048 | search subset | 1 | 1,267 | 26 | 8,567 | 160,649 | 189,025 |
| base_vmm | greedy-entry | 4096 | search subset | 1 | 1,826 | 26 | 14,499 | 154,826 | 189,134 |
| transfer_vmm | greedy-entry | 4096 | all training | 1 | 2,284 | 11 | 18,138 | 151,453 | 189,400 |
| transfer_vmm | greedy-entry | 4096 | search subset | 2 | 1,285 | 19 | 8,709 | 160,908 | 189,426 |
| transfer_vmm | greedy-entry | 4096 | search subset | 3 | 1,302 | 21 | 8,793 | 160,950 | 189,552 |
| transfer_vmm | greedy-byte | 4096 | search subset | 1 | 1,411 | 26 | 9,075 | 160,699 | 189,583 |
| revival_only_vmm | greedy-entry | 4096 | search subset | 1 | 1,438 | 26 | 10,341 | 159,451 | 189,601 |
| transfer_vmm | bpe | 4096 | search subset | 1 | 1,339 | 26 | 8,474 | 162,321 | 190,604 |
| mdl_prefix_stop | greedy-entry | lane rule (2048) | search subset | 1 | 1,344 | 26 | 9,828 | 162,409 | 192,046 |
| mdl_prefix_stop | greedy-entry | 4096 | search subset | 1 | 1,344 | 26 | 9,828 | 162,409 | 192,046 |
| transfer_vmm | greedy-entry | 1024 | search subset | 1 | 955 | 26 | 6,258 | 167,677 | 193,744 |

`w3-commit-subjects` (6,300 validation records, 374,475 raw bytes):

| Selection | Chain | K | Fit records | Seed | Entries | Added | Model | Payload | Total |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| transfer_vmm | greedy-entry | 4096 | all training | 1 | 1,983 | 5 | 14,227 | 166,197 | 205,633 |
| transfer_vmm | greedy-entry | 4096 | search subset | 3 | 1,157 | 13 | 7,080 | 175,209 | 207,498 |
| transfer_vmm | greedy-entry | 4096 | search subset | 1 | 1,161 | 10 | 7,074 | 175,300 | 207,583 |
| transfer_vmm | greedy-entry | 4096 | search subset | 2 | 1,163 | 14 | 7,099 | 175,390 | 207,698 |
| transfer_vmm | bpe | 4096 | search subset | 1 | 1,244 | 10 | 7,082 | 177,369 | 209,660 |
| mdl_prefix_stop | greedy-entry | lane rule (1024) | search subset | 1 | 1,024 | 10 | 6,594 | 179,494 | 211,297 |

"Search subset": 2,048 training records, the ones whose index `i` has the smallest
`sha256("bits-freeze-subset:<seed>:<i>")`. "All training": the search still runs on that subset, and
the selector and code tables get every training record.

### Baseline tuning so far (validation, all-in bytes, 4 index bytes per record)

Tool: `unfinished-freeze-tools/tune_baselines.py`. The harness's grid `full`, its dictionary trainers
and its encoders; each setting fitted on the whole training input and measured on the validation
records (model bytes plus stored bytes; ties to the smaller model, then the earlier grid position).
Every setting tried is in `progress-data/baseline-tuning-so-far.json`.

**Not searched:** for the zstd methods, dictionaries of kind `cover` were tried only at the (level,
size) of the two best `fastcover` settings of each per-record method, and not at all for the
small-block methods (188 or 186 of 276 settings). A rerun with the twelve best was started and
stopped by the pause. The DEFLATE grid was searched in full (106 of 106). The harness's own 4-fold
selection was not run.

| Method | `w1-short-files` | `w2-message-entries` | `w3-commit-subjects` |
|---|---|---|---|
| `raw-indexed` | 559,441 | 415,007 | 399,691 |
| `zstd-lean-frame-tuned` | 288,917 (level 9, cover, 12288) | 276,562 (level 3, fastcover, 8192) | 313,559 (level 1, cover, 8192) |
| `zstd-raw-block-tuned` | 275,024 (level 9, cover, 12288) | 250,620 (level 3, fastcover, 8192) | 281,789 (level 1, cover, 8192) |
| `deflate-raw-tuned` | 283,415 (level 9, zstd-fastcover-content, 16384) | 241,523 (level 9, zstd-cover-content, 12288) | 267,667 (level 6, zstd-cover-content, 12288) |
| `fsst-reference` | 352,063 | 253,017 | 253,887 |
| `zstd-lean-frame-blocks-of-2` | 261,498 (level 9, fastcover, 12288) | 246,039 (level 9, fastcover, 8192) | 286,438 (level 1, fastcover, 8192) |
| `zstd-lean-frame-blocks-of-4` | 235,010 (level 15, fastcover, 12288) | 213,966 (level 9, fastcover, 8192) | 247,667 (level 9, fastcover, 8192) |
| `zstd-lean-frame-blocks-of-8` | 217,021 (level 15, fastcover, 6144) | 197,882 (level 9, fastcover, 8192) | 228,847 (level 9, fastcover, 8192) |
| `zstd-lean-frame-blocks-of-16` | 200,466 (level 22, fastcover, 6144) | 187,573 (level 9, fastcover, 8192) | 218,278 (level 9, fastcover, 8192) |

### Where validation stands (provisional, decides nothing)

Smallest candidate total so far against the smallest per-record baseline so far. The gate needs a
ratio of at most 0.90 on both `w1` and `w2`, and a lookup condition that was not measured at all.

| Workload | Smallest per-record baseline | Smallest candidate | Ratio | Lane's MDL prefix stop, lane's budget rule |
|---|---:|---:|---:|---:|
| `w1-short-files` | 275,024 (`zstd-raw-block-tuned`) | 249,843 | 0.908 | 264,328 (0.961) |
| `w2-message-entries` | 241,523 (`deflate-raw-tuned`) | 187,247 | 0.775 | 192,046 (0.795) |
| `w3-commit-subjects` (spare) | 253,887 (`fsst-reference`) | 205,633 | 0.810 | 211,297 (0.832) |

On `w1` the bytes condition is not met by any configuration tried. A wider `cover` search can only
lower the baseline totals. The candidate rows differ by seed by 0.3 to 0.8% and by chain by up to 2%.

## Not done

- `score.py` and `assemble_freeze.py` in `unfinished-freeze-tools/` have **never been executed**.
  They parse and import. Treat them as drafts.
- No dry run on validation, no repeat run to compare archive hashes, no lookup timing of any method,
  no measurement of reader memory or cold start.
- The byte accounting is drafted (total is the serialised archive with one 4-byte offset per record
  for every method, the harness's `all_in`) and was used above, but was not confirmed through the
  scoring script.
- The decision rule's timing details exist only as draft constants in `assemble_freeze.py`: 400,000
  lookups per round, 9 interleaved rounds, the 95th percentile across records of per-record mean
  lookup time, median over rounds, a load-average rule for the quiet window. None was tried.
- Candidate configurations queued and not run: `transfer_vmm` greedy-entry with all training records
  at K 2048 (`w2`) and K 1024 (`w1`, `w2`); `w3` search subset at K 2048 and 1024; `w1` chain `bpe`
  with seeds 2 and 3; chain `bpe` with all training records (`w1`, `w2`); and for `w3` with all
  training records: seeds 2 and 3, chain `bpe`, K 2048, K 1024, plus MDL prefix stop at K 4096.
  Budgets 256 and 512 were not tried.
- After the tools were moved into `unfinished-freeze-tools/`, only an import check was made. The
  five tools that had been run were run from the parent directory.

## Next steps for whoever resumes

1. Confirm the hashes in the table above still hold. If a lane or harness file changed, the
   measurements here do not carry over.
2. Rerun `tune_baselines.py` for the three workloads with a wider `cover` search (`--cover-top 12
   --cover-top-blocks 2`, or the whole grid in a quiet period; a `cover` dictionary at level 19 or
   22 costs about a minute of processor time each on these training inputs).
3. Run the queued candidate configurations with `explore_candidate.py`, appending to a copy of
   `progress-data/candidate-configurations-tried.jsonl`. Fix the list before looking at more
   results, then stop adding.
4. Run `score.py run --sizes-only` on one workload with a hand-made draft freeze file to debug the
   script before trusting it. Check that its totals equal the tables above.
5. Decide the open points in the draft rule: the quiet-window threshold, and whether the per-record
   mean statistic is acceptable in place of a percentile of single timings (the timer step is 41 ns).
6. Assemble `FREEZE.json` (`assemble_freeze.py` picks, per workload, the smallest validation total
   among configurations verified in both readers, and the first-ranked setting per baseline), run
   the dry run on validation for all three workloads, run it a second time and compare archive
   hashes, then write the notes.
7. Environment: `FAIR_BASELINES_FSST_SRC` set to the reference FSST checkout in the custody
   directory, `FAIR_BASELINES_BUILD_DIR` set to a scratch directory. `BITS_ADAPTER_CACHE_DIR` may be
   set while exploring; it stores fitted dictionaries, which are pieces of records, so it must point
   outside the repository.

## What makes the comparison awkward

1. **`engine.c` reads at most 2,048 files** and the lane's recipe gives it one record per file. The
   training sets have 5,700, 9,750 and 12,600 records. The search therefore sees 36%, 21% and 16% of
   them, while every baseline is fitted on all of them. Giving the selector all training records at
   K 4096 was worse on `w1` and `w2` and better on `w3`; at K 2048 on `w1` it was slightly better.
2. **The selector sizes the dictionary for the records it is fitted on**, not for the number of
   records to be stored. The baselines' dictionary size is tuned directly on validation.
3. **Single bytes missing from the dictionary are added at encode time**, and the code lengths are
   rebuilt with them. The archive's model therefore depends on which bytes the encoded records
   contain. The additions are inside the archive and counted. Cost on validation, `w1`, K 4096:
   27 bytes added, 81 model bytes, 76 occurrences in 22 records, 1,281 payload bits.
4. **The two-table layout cannot be used**: it needs each record assigned to one of two known groups
   stored as two runs.
5. **One index form**: a 4-byte bit offset per record, with 16-bit record and entry counts. The
   harness can give the baselines a 3-byte index; the candidate's container cannot have one.
6. **The lane's scripts give the search an 8-second wall-clock limit** and use whatever exists when
   it runs out. On a busy machine the lane's own numbers changed between two runs on the same
   records (for example 12,412 and 12,437 bytes for one row). The adapter requires a completed
   search and fails otherwise.
7. **The C reader** has fixed tables for 4,100 symbols, takes no output capacity, reads past the
   end of the stream (the lane's program pads the loaded file with 64 zero bytes) and calls `exit()`
   on a bad header. The shim checks the header and pads a private copy. A dictionary plus added bytes above 4,099 entries cannot be read.
8. **The lane's MDL prefix-stop builder returns sizes, not the dictionary**, and needs held-out
   records to run. The adapter hands it one fit record as a stand-in and reruns the search to cut
   the chain at the selected length, as the lane's benchmark script does.
9. **Build cost**: fitting takes tens of seconds to minutes of pure Python per workload, against
   seconds for the baselines.

## Files left

- `FREEZE-PROGRESS.md`: this file.
- `unfinished-freeze-tools/`: `bits_adapter.py`, `bits_native_shim.c`, `freeze_common.py`,
  `tune_baselines.py`, `explore_candidate.py`, `check_adapter_fidelity.py` (all run), `score.py`,
  `assemble_freeze.py` (never run).
- `unfinished-freeze-tools/progress-data/`: `candidate-configurations-tried.jsonl`,
  `baseline-tuning-so-far.json`, `adapter-fidelity-old-suites.json`. Settings, counts and hashes only.

Fitted dictionaries, search chains and logs are in the freeze owner's scratch directory, outside the
repository. They can be rebuilt from the training records and may not survive a cleanup.
