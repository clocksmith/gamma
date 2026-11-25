# Fair baselines for short-record random access (`fair-baselines-v1`)

An independent baseline harness for the single-record random-access comparison in
[`../rung2-short-ra-bench-v1`](../rung2-short-ra-bench-v1/README.md), and one diagnostic run with it.

The harness was written by a party other than the BITS author. It does not read or import the
BIT3 or TransferVMM encoders. Every BIT3 number on this page is copied from the lane's committed
results file; BIT3 was not run here.

## Status of the numbers on this page

The diagnostic below is **not a decision test**. The held-out halves of the lane's suites were
already used while the lane's codec was designed, so nothing here is evidence about unseen data.
It answers one narrower question: how much of the reported gap between BIT3 and zstd on the
short-record suites is per-record frame overhead, and whether the reference FSST behaves like the
lane's own FSST.

Two further limits, both described in detail below:

- The lane's suites could not be rebuilt exactly. They are sampled from live working trees of
  other repositories, and files were removed from those trees after the committed run.
- Timings were taken on a loaded machine. They are indicative only and must be repeated in a
  quiet window before they are used for a decision. Sizes do not depend on machine load.

## What is measured

For every method, on the same training records and the same test records:

- **Archive size**, split into header, model (dictionary or symbol table), index, per-record
  framing and payload. The five parts are measured from the serialized archive and must sum to its
  length.
- **Exact reconstruction**: every test record is decoded on its own, in random order, from the
  serialized archive, and compared with the original bytes.
- **Lookup time** for one record, in memory, with one native loop shared by all methods.
- **Reader heap** (decoder contexts, tables, scratch buffers), counted by allocator hooks.
- **Build cost** as wall time: tuning plus final fit, and encoding the test records.

## What is not measured

- Disk or network reads. Everything is in memory; do not compare these lookups with a disk read.
- Peak memory while building (training and encoding).
- Stack use of the readers.
- Lookup time of a candidate that has no native decoder is taken in a Python loop and is labelled
  as not comparable.
- Cold-start cost (opening the archive, building decoder tables) is not part of the lookup time.
- zstd advanced compression parameters (minimum match, window, strategy overrides), other DEFLATE
  implementations (libdeflate, zopfli) and FSST12 were not tried. "Tuned" here means level,
  dictionary kind and dictionary size.

## Files

| file | purpose |
|---|---|
| `run_fair_baselines.py` | command line: train input, test input, results JSON |
| `fb_core.py` | record loading, the archive container, byte accounting |
| `fb_codecs.py` | the baselines and their training-only tuning |
| `fb_measure.py` | build, account, verify, time; results document |
| `fb_native.py`, `native/` | C helper (zstd, DEFLATE, FSST readers; encoders; the timing loop), built outside the repository |
| `fb_candidate.py`, `examples/` | plug-in point for a candidate codec, with a worked example |
| `lane_suites.py`, `run_lane_diagnostic.py` | rebuild the lane's suites and run the diagnostic |
| `test_fair_baselines.py` | unit tests |
| `results/` | diagnostic results (JSON and the tables below) |

## Running it

Requirements: Python 3.10+, a C and C++ compiler, zstd 1.5.x headers and library, zlib. The
reference FSST is not vendored; fetch it yourself:

```bash
git clone --depth 1 https://github.com/cwida/fsst.git /some/scratch/fsst      # MIT licence
export FAIR_BASELINES_FSST_SRC=/some/scratch/fsst
export FAIR_BASELINES_BUILD_DIR=/some/scratch/fb-build     # optional; default is the system temp directory

python3 -B test_fair_baselines.py

python3 -B run_fair_baselines.py --train TRAIN --test TEST --out results/my_run.json
```

`TRAIN` and `TEST` are separate paths. Each is either a directory with one record per file (files
sorted by relative path; a first-level subdirectory name becomes the record's group) or a JSONL
file whose lines are a JSON string, or an object with `"text"` (UTF-8) or `"base64"` and an
optional `"group"`.

Without the FSST sources the reference FSST baseline reports `not-applicable` and says why. The
lane's own FSST implementation still runs, under the name `fsst-lane-own-impl`.

Useful options: `--grid quick` (smaller tuning grid), `--methods a,b`, `--no-timing`,
`--lookups N`, `--rounds N`, `--block-sizes 2,4,8,16`, `--candidate file.py:Class`.

## Methods

| name | what it is |
|---|---|
| `raw-indexed` | uncompressed records plus index |
| `zstd-frame-lane-rule` | zstd -19, one standard frame per record, no checksum; dictionary from `zstd --train` defaults; size picked from {0, 1, 2, 4, 8} KiB by the smallest archive of the *training* records. This reproduces the lane's rule and is a reference point only |
| `zstd-frame-tuned` | same framing, settings chosen by cross-validation |
| `zstd-lean-frame-tuned` | magicless frame, no content size, no checksum, no dictionary ID: 2 header bytes and 3 block-header bytes per record |
| `zstd-raw-block-tuned` | raw zstd block with a preloaded dictionary and no frame (`ZSTD_compressBlock` / `ZSTD_decompressBlock`, deprecated but present in 1.5.7). One flag bit per record marks a record zstd declined to compress |
| `deflate-raw-lane-rule` | raw DEFLATE level 9 (`wbits=-15`), preset dictionary picked by the lane's rule |
| `deflate-raw-tuned` | raw DEFLATE, settings chosen by cross-validation |
| `fsst-reference` | [cwida/fsst](https://github.com/cwida/fsst) (`fsst_create`, `fsst_compress`, `fsst_decompress`); the model is the `fsst_export()` bytes |
| `fsst-lane-own-impl` | the lane's `fsst255_codec.py`, called as its benchmark calls it; decoded in Python |
| `.../per-group` | one independently tuned model per record group (see below) |
| `zstd-lean-frame-blocks-of-N` | one lean zstd frame per block of N consecutive records, N in 2, 4, 8, 16; reported in a separate table with the raw bytes that must be decoded per lookup |

The `per-group` variants exist because the lane's BIT3 builder is handed the two halves of a
suite separately (for example WGSL files and JSON files) and has a layout with one Huffman table
and one stream per half. A per-group baseline gets the equivalent: one model per group, groups
stored contiguously.

## Tuning

Settings are chosen on the training input only.

- The training input is split into 4 folds (seeded shuffle). For each setting the model is fitted
  on three folds and the stored bytes of the fourth are measured; this is summed over the four
  folds. Every training record is validated exactly once, so the sum estimates the stored bytes of
  an archive that holds as many unseen records as the training input. The mean model size is added
  once. The smallest total wins.
- The final model is refitted on the whole training input with the chosen setting, and the test
  records are encoded once.
- zstd grid: levels 1, 3, 9, 15, 19, 22; no dictionary, or a dictionary of 256 bytes to 112 KiB
  (sizes above the training volume are dropped) of three kinds: `fastcover` (what `zstd --train`
  does), `cover` (`zstd --train-cover`, parameter search), and `raw-sample` (whole training records
  taken at an even stride, last N bytes kept, loaded as raw content).
- DEFLATE grid: levels 6 and 9, memory level 9; no dictionary, or up to 32 KiB of: a zstd-trained
  dictionary as is (what the lane does), a zstd-trained dictionary with its header stripped, or a
  raw sample.
- zstd-trained dictionaries get their samples in the order the zstd command line uses (a
  fixed-seed shuffle). With that order the helper's dictionaries are byte-identical to the CLI's;
  a unit test checks this when the CLI is installed.
- FSST has no settings to tune; its symbol table is built from all training records.

## Byte accounting

All baselines use one container, so the accounting has the same form for every method:

| part | what goes in it |
|---|---|
| header | 16 bytes: tag, method, index width, model kind, records per block, record count, model length |
| model | dictionary or symbol table, as stored |
| index | one end offset per stored unit (and one raw end offset per record for the block method) |
| framing | bytes inside a stored unit that are container format: zstd magic, frame header, block headers, checksum; the stored-raw flag bitmap of the raw-block method. zstd frames are parsed to measure this |
| payload | the rest of the stored units |

Raw DEFLATE has no byte-level framing; its 3-bit block header, end-of-block code and bit padding
are inside the payload bytes.

Three totals are reported per method:

- **like-for-like**: the size in the lane's own container form: 10-byte header, model, 4 index
  bytes per record, stored units. This is the number to put next to the lane's `held_out_bytes`.
- **all-in**: the serialized archive of this harness with 4 index bytes per offset. It differs
  from like-for-like only by the header (16 bytes against 10).
- **all-in, compact index**: the same archive with the smallest whole-byte offset width that fits.
  The same rule is applied to every method.

### What the lane's `held_out_bytes` counts

Read from `run_ra_pareto_bench.py`, `fsst255_codec.py` and the archive parsers in
`ra_codecs_bench.c`: for all four codecs `held_out_bytes` is the length of one self-contained
blob. It includes the container header (8 to 10 bytes), the dictionary or symbol table, the code
lengths (BIT3), 4 index bytes per record, and the stored records. So it already counts everything
a reader needs, and like-for-like and all-in mean the same thing up to header size.

What the number reflects beyond the codec itself:

- The zstd baseline stores a full frame per record: magic, frame header with a 4-byte dictionary
  ID and the content size, and a block header. That is 13 bytes per record under 256 bytes and 14
  above.
- The zstd and DEFLATE dictionary size is picked by the size of the archive of the *training*
  records, which the dictionary was trained on, from {0, 1, 2, 4, 8} KiB only; the zstd level is
  fixed at 19.
- BIT3's stored dictionary is completed at encode time with any single byte that occurs in the
  held-out records but not in the trained dictionary. Those bytes are counted, but the stored
  model depends on the held-out records.
- BIT3's two-table layout is built from the two groups of a suite separately; the lane's
  baselines were trained on the merged groups.
- The FSST baseline is the lane's own implementation, not the reference one.

## Verification

A reader is opened on the serialized archive bytes alone. Every test record is decoded on its
own, in a seeded random order, and compared with the original. This is done for both index
representations. A method with any difference is reported as `failed-verification` and gets no
timing. A candidate with a native decoder is verified through that decoder as well.

## Timing

One loop in `native/fb_native.c` (`fb_time_lookups`) is used for every method. It calls the
method's decode function through a function pointer, with pseudo-random record indexes, writing
into one output buffer. A candidate's native decoder is called through the same pointer type from
the same loop.

- `loop_mean_ns`: total time of 200,000 lookups divided by 200,000, with the timer read only
  before and after the loop. The run is repeated (5 rounds by default) and the lowest round is
  reported, as the one least disturbed by other work; all rounds are in the JSON.
- `per_record_mean_median_ns`, `per_record_mean_p95_ns`: the same lookups timed one by one; for
  each record the mean of its timings is taken, then the median and 95th percentile across
  records. A sample longer than 8 times its record's mean plus 2 microseconds is treated as an
  interrupted lookup and left out of that mean; the count is reported.
- `single_lookup_median_ns`, `single_lookup_p95_ns`: percentiles of the individual timings. On
  Apple silicon the timer advances in steps of about 42 ns, so these are multiples of that step
  and are coarse for methods that take less than a few steps. The per-record means do not have
  this problem, because averaging many quantized readings recovers the mean.

These numbers are not the lane's numbers and should not be mixed with them: the lane times each
codec in its own process with its own loop and reports a mean only.

## Memory and build cost

- `reader_heap_peak_bytes`: bytes allocated by the reader, counted by hooks passed to zstd
  (`ZSTD_customMem`) and zlib (`zalloc`), plus the harness's own reader structures. The archive
  bytes are reported separately. Stack is not counted.
- `tune_and_fit_sec`, `encode_test_sec`: wall time. Dictionaries are cached across the methods of
  one run; when a method reuses a dictionary another method trained, the original training time is
  added to its cost, so the reported cost does not depend on the order the methods ran in.

## Candidate plug-in

A candidate codec is a small Python class with `train`, `encode` and `open`, optionally backed by
a native decoder with three C functions. See the header of `fb_candidate.py` for the interface
and `examples/candidate_example.py` for a working example.

```bash
python3 -B run_fair_baselines.py --train TRAIN --test TEST --out results/with_candidate.json \
    --candidate path/to/adapter.py:ClassName
```

The harness checks that the candidate's byte categories sum to its archive length and verifies
every record through the candidate's reader. It takes on trust how the candidate splits its bytes
between the categories.

## Diagnostic on the lane's suites

```bash
# sample the suites as the lane does, export them outside the repository, measure
python3 -B run_lane_diagnostic.py --work-dir <directory outside the repository> \
    --fsst-src <fsst checkout> --check-with-lane-code
# measure the same exported records again, with more timing rounds (this run is the one in results/)
python3 -B run_lane_diagnostic.py --work-dir <same directory> --fsst-src <fsst checkout> \
    --reuse-exported --check-with-lane-code --rounds 9
# rewrite the tables from the JSON
python3 -B run_lane_diagnostic.py --render-only
```

Outputs: [`results/lane_suites_diagnostic_v1.json`](results/lane_suites_diagnostic_v1.json) (everything, including
chosen settings and the byte breakdown of every method) and
[`results/lane_suites_diagnostic_v1.md`](results/lane_suites_diagnostic_v1.md) (the tables below plus one table per suite).
Both runs produced identical sizes.

### Three things to know before reading the tables

1. **This is not a decision test.** The held-out halves of these suites were already used during
   the lane's design. The tables say something about the framing question on these suites and
   nothing about unseen data.
2. **The record sets are close to the committed run's, but not the same.** The lane samples its
   suites from live working trees and keeps no manifest. The sampler here returns exactly what
   the lane's own sampler returns today (pool digests are equal, checked in a child process), but
   the held-out byte totals differ from the committed run: 23,924 against
   23,837, 24,245 against 24,180, and 60,187 against 58,759.
   Putting every tracked file that changed since the committed run back to its earlier committed
   version does not change the totals. A build-output directory in one sampled tree was emptied
   after the committed run; that is the likely cause, and those files cannot be restored. Running
   the lane's own three
   baselines by the lane's own rule on the rebuilt records shows how far apart the sets are
   (rebuilt minus committed, bytes):

   | lane baseline, lane rule | `short_wgsl_vs_json_80_to_80` | `short_ts_vs_mjs_80_to_80` | `med_ts_vs_json_50_to_50` |
   |---|---:|---:|---:|
   | zstd full frame | +1 | -192 | +379 |
   | DEFLATE | +23 | -294 | +400 |
   | FSST (lane's implementation) | +81 | -62 | +1,040 |

   Every "difference from BIT3" below therefore compares a baseline on the rebuilt set with BIT3
   on the committed set. On the first suite the two sets nearly coincide. On the second, the
   rebuilt set is easier for the three reproduced baselines by 62 to 294 bytes, so that column
   favours the baselines by an unknown amount of that order. The comparison becomes exact only
   when BIT3 is run through the plug-in on the same exported records.
3. **Timings were taken on a loaded machine** (one-minute load average 19.91, 6.83 and 7.76 when the
   three suites finished, with other timed work running on the same machine). They are indicative
   only and must be repeated in a quiet window before they are used for any decision.

### Sizes

Like-for-like bytes (the lane's container form: 10-byte header, model, 4 index bytes per record,
stored records), with the difference from BIT3's committed number in brackets.

| | `short_wgsl_vs_json_80_to_80` | `short_ts_vs_mjs_80_to_80` | `med_ts_vs_json_50_to_50` |
|---|---:|---:|---:|
| held-out records, raw bytes (rebuilt) | 160, 23,924 | 160, 24,245 | 100, 60,187 |
| held-out records, raw bytes (committed run) | 160, 23,837 | 160, 24,180 | 100, 58,759 |
| lane, committed: BIT3 | 12,092 (+0) | 12,390 (+0) | 30,109 (+0) |
| lane, committed: FSST-255 (lane's own implementation) | 14,618 (+2,526) | 14,929 (+2,539) | 37,646 (+7,537) |
| lane, committed: DEFLATE raw + dictionary | 12,842 (+750) | 13,458 (+1,068) | 27,664 (-2,445) |
| lane, committed: zstd -19 full frame + dictionary | 14,678 (+2,586) | 15,459 (+3,069) | 27,426 (-2,683) |
| this harness: `raw-indexed` | 24,574 (+12,482) | 24,895 (+12,505) | 60,597 (+30,488) |
| this harness: `zstd-frame-lane-rule` | 14,679 (+2,587) | 15,267 (+2,877) | 27,805 (-2,304) |
| this harness: `zstd-frame-tuned` | 14,031 (+1,939) | 15,155 (+2,765) | 27,519 (-2,590) |
| this harness: `zstd-lean-frame-tuned` | 12,751 (+659) | 13,867 (+1,477) | 26,619 (-3,490) |
| this harness: `zstd-raw-block-tuned` | 11,971 (-121) | 13,087 (+697) | 26,136 (-3,973) |
| this harness: `deflate-raw-lane-rule` | 12,865 (+773) | 13,164 (+774) | 28,064 (-2,045) |
| this harness: `deflate-raw-tuned` | 12,316 (+224) | 12,816 (+426) | 27,884 (-2,225) |
| this harness: `fsst-reference` | 14,084 (+1,992) | 14,576 (+2,186) | 38,474 (+8,365) |
| this harness: `fsst-lane-own-impl` | 14,699 (+2,607) | 14,867 (+2,477) | 38,686 (+8,577) |
| this harness: `zstd-lean-frame-tuned/per-group` | 12,733 (+641) | 13,871 (+1,481) | 26,555 (-3,554) |
| this harness: `zstd-raw-block-tuned/per-group` | 11,953 (-139) | 13,282 (+892) | 26,067 (-4,042) |
| this harness: `deflate-raw-tuned/per-group` | 12,298 (+206) | 13,579 (+1,189) | 27,955 (-2,154) |
| this harness: `fsst-reference/per-group` | 13,402 (+1,310) | 14,490 (+2,100) | 37,371 (+7,262) |
| this harness: `zstd-lean-frame-blocks-of-2` | 11,920 (-172) | 12,704 (+314) | 25,939 (-4,170) |
| this harness: `zstd-lean-frame-blocks-of-4` | 10,912 (-1,180) | 11,860 (-530) | 25,040 (-5,069) |
| this harness: `zstd-lean-frame-blocks-of-8` | 10,082 (-2,010) | 11,186 (-1,204) | 24,062 (-6,047) |
| this harness: `zstd-lean-frame-blocks-of-16` | 9,584 (-2,508) | 10,605 (-1,785) | 22,492 (-7,617) |

### What the sizes show

Framing:

- The lane-style zstd archive spends 2,080 and 2,088 bytes on frame and block headers on the two short
  suites (13 or 14 bytes for each of 160 records, measured by parsing the frames). The committed
  gap between zstd and BIT3 there is 2,586 and 3,069 bytes. Subtracting the measured framing
  from the lane's own committed zstd number leaves +506 and +981 bytes against BIT3.
- `short_wgsl_vs_json_80_to_80`: zstd stored as raw blocks and tuned on the training input is
  11,971 bytes, 121 bytes smaller than BIT3's committed 12,092. With the magicless frame
  (5 bytes per record) it is 12,751, 659 bytes larger. Tuned DEFLATE is 12,316, 224 bytes larger.
- `short_ts_vs_mjs_80_to_80`: BIT3's committed 12,390 is smaller than every per-record baseline:
  tuned DEFLATE 12,816 (426 larger), raw-block zstd 13,087 (697 larger), magicless-frame zstd
  13,867 (1,477 larger). Point 2 above applies to this suite in particular.
- One model per group changes raw-block zstd by -18 and +195 bytes on the short suites.
- `med_ts_vs_json_50_to_50`: zstd was already smaller than BIT3 in the lane's numbers; without frames it
  is 26,136 against BIT3's committed 30,109.

So frame overhead is most of the zstd gap on both short suites. Removing all of it puts zstd
slightly below BIT3 on one short suite and leaves BIT3 several hundred bytes ahead on the other.
The magicless frame alone does not close the gap on either.

FSST:

- On the same records the reference FSST is 615, 291 and 212 bytes smaller than the lane's
  implementation. The difference is the stored table (671 against 1,464 bytes on the first
  suite); the reference payload is slightly larger (12,763 against 12,589).
- The reference FSST stays 1,992 and 2,186 bytes larger than BIT3's committed numbers on the short
  suites (1,310 and 2,100 with one table per group).

Small blocks:

- Two records per block: 11,920 and 12,704 bytes on the short suites; four per block: 10,912 and
  11,860. A lookup then decodes about 300 or 600 raw bytes instead of about 150.

### Lookup time (indicative only)

Nanoseconds per single-record lookup, in memory: loop mean (best of 9 rounds) / median of
per-record means / 95th percentile of per-record means. Taken on a loaded machine; repeat in a
quiet window before using them for a decision. The lane's committed ns/seek are from its own
loop on another occasion and are listed only for reference; they are means, and are not
comparable with the rows below them. `fsst-lane-own-impl` is decoded in Python here.

| | `short_wgsl_vs_json_80_to_80` | `short_ts_vs_mjs_80_to_80` | `med_ts_vs_json_50_to_50` |
|---|---:|---:|---:|
| lane, committed (mean only): BIT3 | 227 | 226 | 889 |
| lane, committed (mean only): FSST-255 (lane's own implementation) | 50 | 53 | 194 |
| lane, committed (mean only): DEFLATE raw + dictionary | 513 | 374 | 1,387 |
| lane, committed (mean only): zstd -19 full frame + dictionary | 194 | 198 | 750 |
| this harness: `raw-indexed` | 16 / 14 / 15 | 13 / 11 / 12 | 18 / 14 / 16 |
| this harness: `zstd-frame-lane-rule` | 683 / 379 / 788 | 199 / 142 / 390 | 773 / 730 / 1,431 |
| this harness: `zstd-frame-tuned` | 278 / 239 / 529 | 225 / 217 / 414 | 816 / 729 / 1,458 |
| this harness: `zstd-lean-frame-tuned` | 277 / 236 / 528 | 222 / 214 / 417 | 818 / 733 / 1,447 |
| this harness: `zstd-raw-block-tuned` | 258 / 225 / 509 | 210 / 199 / 404 | 807 / 721 / 1,439 |
| this harness: `deflate-raw-lane-rule` | 513 / 310 / 1,679 | 368 / 298 / 671 | 1,555 / 1,709 / 2,243 |
| this harness: `deflate-raw-tuned` | 511 / 324 / 1,667 | 366 / 303 / 685 | 1,749 / 1,813 / 2,378 |
| this harness: `fsst-reference` | 40 / 35 / 58 | 44 / 36 / 66 | 145 / 140 / 207 |
| this harness: `fsst-lane-own-impl` | 5,799 / 5,166 / 10,542 (Python loop) | 6,528 / 5,667 / 12,375 (Python loop) | 29,371 / 27,542 / 44,708 (Python loop) |
| this harness: `zstd-lean-frame-tuned/per-group` | 279 / 257 / 473 | 233 / 215 / 449 | 818 / 753 / 1,211 |
| this harness: `zstd-raw-block-tuned/per-group` | 261 / 239 / 459 | 230 / 204 / 420 | 844 / 784 / 1,281 |
| this harness: `deflate-raw-tuned/per-group` | 546 / 352 / 1,945 | 457 / 347 / 1,690 | 1,880 / 1,852 / 2,504 |
| this harness: `fsst-reference/per-group` | 41 / 33 / 61 | 44 / 34 / 62 | 152 / 140 / 214 |
| this harness: `zstd-lean-frame-blocks-of-2` | 372 / 355 / 641 | 417 / 399 / 670 | 1,607 / 1,516 / 2,282 |
| this harness: `zstd-lean-frame-blocks-of-4` | 919 / 877 / 1,377 | 783 / 729 / 1,117 | 3,406 / 3,417 / 5,259 |
| this harness: `zstd-lean-frame-blocks-of-8` | 1,347 / 997 / 2,307 | 1,433 / 1,406 / 1,922 | 5,916 / 5,558 / 7,492 |
| this harness: `zstd-lean-frame-blocks-of-16` | 2,384 / 1,871 / 4,936 | 3,208 / 2,964 / 4,226 | 9,171 / 9,624 / 10,367 |
