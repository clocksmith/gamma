# Golden-byte accounting for short-record codecs (`short-record-byte-accounting-v1`)

An independent byte accountant and a hand-checked golden fixture for the short-record
random-access comparison. A codec result is accepted only if its reported size covers every byte a
reader needs to return one record: header, dictionary, model or code tables, the random-access
index and per-record framing, as well as the payload. If any of those is left out, the check fails.

This directory imports nothing from `../fair-baselines-v1`, `../rung2-short-ra-bench-v1`,
`../short-record-decision-v1` or any codec. It uses the Python standard library only. It runs no
benchmark and reads no test set.

## Why it is a separate directory

The harness a future codec claim runs through is `../fair-baselines-v1` (the baseline author's
harness, with the plug-in point `fb_candidate.py`), scored by
`../short-record-decision-v1/unfinished-freeze-tools/score.py`. Both are part of the paused freeze:
`../short-record-decision-v1/FREEZE-PROGRESS.md` records the SHA-256 of every `fair-baselines-v1`
source file and requires those hashes to still hold when the work resumes, and `score.py` is the
freeze owner's draft. Editing either would invalidate the freeze progress, so neither was changed.
The accountant is not yet wired into them; see "Required call" below.

## Files

| file | purpose |
|---|---|
| `byte_accountant.py` | the accountant: measures an artifact set, checks a producer report, leakage guard, command line |
| `golden/gold1/records/` | three test records, committed as bytes |
| `golden/gold1/artifacts/` | those records in the `gold1` reference encoding, written by hand with `printf`, plus `artifacts.json` |
| `golden/gold1/expected.json` | the expected breakdown, derived by hand from the format below |
| `test_byte_accountant.py` | tests |

## Running the tests

```bash
python3 -B test_byte_accountant.py
python3 -B -m pytest -p no:cacheprovider test_byte_accountant.py     # if pytest is installed
```

## What the accountant does

Input: one directory holding the artifact files a codec emitted, plus `artifacts.json`, which gives
each file's role. The accountant reads the files and measures them. It never uses the producer's
numbers to compute a size.

- **Total**: the sum of the lengths of every artifact file. Every file in the directory must be
  listed in the manifest, and every listed file must exist. A dictionary kept beside the set but
  left unlisted is an error, not a free byte. The manifest is not counted, so a reader must not
  need it.
- **Components**: `header`, `dictionary`, `model` and `index` files count whole. A `units` file
  holds the stored record units. The accountant splits it into `framing` and `payload` by walking
  it with a framing rule it implements itself (`u8-length-prefix`, `u16le-length-prefix` or
  `uvarint-length-prefix`). The walk must end exactly at the end of the file and give the declared
  record count. An index with `offset_width` and `into` is parsed, and its offsets must be the unit
  boundaries the walk found. An `archive` file is one opaque blob: it counts in full toward the
  total, but its components cannot be checked one by one.
- **Report check** (`check_report`): every component the artifacts hold must appear in the report
  with exactly the measured value. The reported components must sum to the reported total, and the
  reported total must equal the measured total. If a harness has one `model` field that also holds
  the dictionary (as `fair-baselines-v1`'s `all_in` does), pass `model_includes_dictionary=True`.
- **Leakage guard** (`check_leakage`): it fails in either of two cases.
  - A run of at least 8 bytes (`--leak-min-len`) of a test record appears in the stored dictionary
    or model bytes but in no training record.
  - The stored bytes contain a byte value that occurs in test records and in no training record,
    unless they carry the whole 256-value alphabet. This second rule targets the pattern the review
    found in `../rung2-short-ra-bench-v1/run_ra_pareto_bench.py` (the `unseen` single-byte entries
    taken from the test records, around lines 218-219 and 282-283).

  The guard needs the training records. Without them, everything the dictionary shares with the
  test records looks like a leak.

## The `gold1` reference format

All integers are little-endian. A reader needs exactly these four files.

| file | layout | bytes in the fixture |
|---|---|---:|
| `header.bin` | magic `GLD1`, version `u8` = 1, record count `u8`, dictionary entry count `u8` | 4 + 1 + 1 + 1 = **7** |
| `dictionary.bin` | per entry: length `u8`, entry bytes | `fn ` (1 + 3) + `() {}` (1 + 5) = **10** |
| `index.bin` | record count + 1 offsets, `u16`, into `units.bin` (each unit's start, then the end) | 4 x 2 = **8** (0, 7, 14, 25) |
| `units.bin` | per record: length `u8` (framing), then tokens (payload). A token below `0x80` is a literal byte; `0x80 + i` is dictionary entry `i` | framing 3 x 1 = **3**; payload 6 + 6 + 10 = **22** |

The three records:

| record | text | bytes | tokens |
|---|---|---:|---|
| `r0.txt` | `fn main() {}` | 12 | `E0 m a i n E1` (6) |
| `r1.txt` | `fn init() {}` | 12 | `E0 i n i t E1` (6) |
| `r2.txt` | `let x = 1;` | 10 | 10 literals |

Expected breakdown: header 7, dictionary 10, model 0, index 8, framing 3, payload 22, **total
50**, for 34 bytes of records. The tests also decode every record from the four files alone, in
random order, with a reader written from this table.

## Required call for a codec result

The pinned files were not edited, so this is the contract a future scoring run must follow. The
check is required: a result that fails it is not accepted.

1. Write the candidate's and each baseline's archive for the scored records as an artifact set:
   one directory per method, with `artifacts.json`. Split the archive into its header, dictionary,
   model, index and units files where the format allows. Otherwise use one `archive` file. That
   still checks the total, but not the components.
2. Call the accountant on each set, with the method's reported byte breakdown, the scored records
   and the training records:

   ```python
   import byte_accountant as BA          # this directory; copy it next to the scorer if preferred
   BA.require(artifact_dir, method_bytes_all_in,
              test_records=scored_records, train_records=training_records,
              model_includes_dictionary=True)    # raises BA.AccountingError on any problem
   ```

   or, from a shell, `python3 -B byte_accountant.py DIR --report REPORT.json --test TESTDIR
   --train TRAINDIR [--model-includes-dictionary]`. It exits with status 1 on any problem.
3. Compare totals only after every method has passed. If the totals are to decide anything, pin
   this file's SHA-256 with the scorer's.

## Limits

- The accountant counts the bytes that are in the artifact set. It cannot know about bytes a reader
  takes from somewhere else, such as a dictionary compiled into the reader or a table built from a
  constant in the decoder source. The method's author has to put every such byte into a file in
  the set. The golden test shows this is enough for `gold1`, but only for `gold1`.
- The framing split is format-aware for length-prefixed units only. Frame headers inside a zstd or
  DEFLATE unit count as payload unless the producer splits them into their own file.
- The leakage guard sees only verbatim bytes. A transformed copy of test content (reordered,
  re-encoded) passes it.
