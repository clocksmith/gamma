# Scorer log: `objective-holdout-v1`

Written by the scorer session. The scorer took no part in writing the rules or training the dictionaries.
All times are UTC on 2026-11-26, taken from `date -u` on the machine that ran the command, or from the
start and end lines the run wrappers wrote into their logs.

Session start 14:03:46. This log was written at 14:11:40.

## Names used in the commands below

Commands are given as run, with these substitutions so that no machine address, account name or home
directory appears here:

| Placeholder | Stands for |
| --- | --- |
| `REPO` | the repository checkout on the scorer's workstation |
| `HOST` | the scoring host, reached over ssh |
| `S` | the scorer directory on the scoring host |
| `META` | the directory on the scoring host that holds IBM's Python near-duplicate cluster file |
| `EXP` | `S/literals/objective-holdout-v1` |

Nothing was computed on the workstation. It ran only git, ssh, rsync, small file reads and writes, and one
SHA-256 of a 2 KB file.

## Scoring host

- Linux, x86_64, 32 cores, shared with other work.
- `python3 --version`: Python 3.14.4
- `zstd --version`: `*** Zstandard CLI (64-bit) v1.5.7, by Yann Collet ***`
- Virtualenv for `select_fresh_codenet.py` only: Python 3.14.4, pip 25.1.1, pyarrow 26.0.1. Nothing else installed.

## What the scorer read, and what it did not open

Read: `PREREGISTRATION.md`, `FORMAT.md`, `README.md`, `SHA256SUMS-FROZEN` and `.gitignore` at commit
`9d7d54b9e`; `DEVIATIONS.md` at commit `b82e3a89b`; the console output of the frozen commands; the set
manifests and the `out/results-*.json` files (see step 7 for what was looked at before the decoder was
written).

Not opened: `bits_oh.py`, `test_bits_oh.py`, `score.py`, `train_arms.py`, `select_fresh_codenet.py`,
`select_project.py`, `audit_zero_escape_misses.py`, `frozen/train-summary.json`, the contents of
`frozen/train.log` (it was hashed only), and anything in the trainer's directory on the scoring host.

No frozen file was modified. The scorer made no commit and no push.

## Commands, in order

### Step 1. Export the freeze commit (14:04:39 to 14:04:39)

```
git -C REPO archive 9d7d54b9e projects/algorithm_solver/literals/objective-holdout-v1 projects/algorithm_solver/literals/codenet-replication-v1/manifest.json projects/algorithm_solver/literals/codenet-replication-v1/corpus | ssh HOST 'mkdir -p S && tar -x -C S --strip-components=2'
```

Exit status 0 on both sides of the pipe. `S` did not exist before this command.

### Step 2, first run. Frozen checksums (14:04:43): FAILED

```
cd EXP && sha256sum -c SHA256SUMS-FROZEN
```

33 of 34 lines `OK`. One line failed, exit status 1:

```
frozen/train.log: FAILED open or read
sha256sum: frozen/train.log: No such file or directory
sha256sum: WARNING: 1 listed file could not be read
```

The scorer stopped here. No test file had been fetched, no virtualenv made, nothing scored.

Two read-only checks on the workstation (14:04:59):

- `git -C REPO ls-files --error-unmatch projects/algorithm_solver/literals/objective-holdout-v1/frozen/train.log`:
  not known to git at `9d7d54b9e`. `git check-ignore -v` on the same path: `.gitignore:50:*.log`.
- `shasum -a 256 frozen/train.log` on the untracked working-tree copy:
  `3506ba96011e2205b62503766ba9570823ac64ac0423a9792176d46f3acfca6d`, equal to the value listed in
  `SHA256SUMS-FROZEN`. That copy was not sent to the scoring host.

The scorer reported the failure and stopped. It did not choose a fix.

### Fix, made by the trainer side, and re-export (14:06:01 to 14:06:02)

The coordinator replied that the log was now committed in follow-up commit `b82e3a89b` (committer time
14:05:38) together with `DEVIATIONS.md`, and told the scorer to export those two files and rerun step 2 in full.

Before exporting, `git diff --name-status 9d7d54b9e b82e3a89b` showed three added files and no changed file:
`DEVIATIONS.md`, `frozen/train.log`, `zero-escape-miss-audit.json`. `SHA256SUMS-FROZEN` is the same in both
commits. `git show b82e3a89b:…/frozen/train.log | shasum -a 256` gave `3506ba96…acfca6d`.

```
git -C REPO archive b82e3a89b projects/algorithm_solver/literals/objective-holdout-v1/frozen/train.log projects/algorithm_solver/literals/objective-holdout-v1/DEVIATIONS.md | ssh HOST 'tar -x -C S --strip-components=2'
```

Exit status 0 on both sides. Only those two files were exported from `b82e3a89b`. Every other file in `S`
is from `9d7d54b9e`. `zero-escape-miss-audit.json` was not exported.

### Step 2, second run. Frozen checksums (14:06:04): PASSED

```
cd EXP && sha256sum -c SHA256SUMS-FROZEN
```

34 of 34 lines `OK`, exit status 0.

### Step 3. Virtualenv (14:06:07 to 14:06:15)

```
cd S && python3 -m venv S/venv
venv/bin/pip install -q pyarrow
```

Both exit status 0.

Then `sha256sum META/Project_CodeNet-Python.clusters`:
`1e3abffe8f29ebde96c87f33037cca9b6e9806338476f54830b29fafd8444fb1`, the value the scorer was given.

### Step 4. Select the fresh CodeNet set (14:06:22 to 14:06:40)

```
cd EXP && ../../venv/bin/python -I select_fresh_codenet.py --python-clusters META/Project_CodeNet-Python.clusters --work ../../work
```

Run detached. Exit status 0. Console output, complete, with directory names replaced by placeholders:

```
<frozen site>:107: RuntimeWarning: Unexpected value in sys.prefix, expected S/venv, got EXP/../../venv
<frozen site>:107: RuntimeWarning: Unexpected value in sys.exec_prefix, expected S/venv, got EXP/../../venv
python shard 0 read, 456 buffered problems
python shard 1 read, 560 buffered problems
python shard 2 read, 706 buffered problems
python shard 3 read, 895 buffered problems
ranks 0..399 reproduce the frozen manifest exactly
fresh: 200 problems, 400 files, 255472 bytes, ranks 400..600, skipped 1
{"python": {"median": 0.1151, "p95": 0.2483, "max": 0.3544, "files_at_or_above_0.8": 0}, "javascript": {"median": 0.2454, "p95": 0.5436, "max": 0.6755, "files_at_or_above_0.8": 0}}
```

It wrote `corpus/codenet-fresh/` and `sets/fresh.json`. The work directory held 568 MB afterwards: four Python
parquet shards and one JavaScript parquet shard.

### Step 5. Select the project (14:06:49 to 14:06:49)

```
cd EXP && python3 -I select_project.py --work ../../work
```

Run detached. Exit status 0. Console output, complete:

```
project: expressjs/express at 1faf228935aa, 120 eligible, 120 kept, 176742 bytes
```

It wrote `corpus/project/` and `sets/project.json`.

### Step 6. Score the four sets (14:07:00 to 14:07:39)

Run from `EXP`, one after another in this order, from one detached wrapper. All four exit status 0.

| Command | Start | End |
| --- | --- | --- |
| `python3 -I score.py --set frozen/sets/train.json --root .. --out out --jobs 8` | 14:07:00 | 14:07:10 |
| `python3 -I score.py --set frozen/sets/dev.json --root .. --out out --jobs 8` | 14:07:10 | 14:07:21 |
| `python3 -I score.py --set sets/fresh.json --root . --out out --jobs 8` | 14:07:21 | 14:07:31 |
| `python3 -I score.py --set sets/project.json --root . --out out --jobs 8` | 14:07:31 | 14:07:39 |

Console output, complete and unedited:

```
train: 400 files, 259706 bytes, 20 headers, 10.8s
  bpe-K256           entries   255  tokens  155571  complete  134422 B  payload  133476 B  escapes 0
  bpe-K256.xp        entries   246  tokens  155832  complete  134379 B  payload  133476 B  escapes 0
  bpe-K4096          entries  4095  tokens   50435  complete  100349 B  payload   68854 B  escapes 0
  bpe-K4096.xp       entries  2894  tokens   55728  complete   96177 B  payload   73573 B  escapes 0
  bytes-K256         entries   255  tokens  135200  complete  116952 B  payload  115785 B  escapes 0
  bytes-K4096        entries  1579  tokens   59608  complete   85587 B  payload   71637 B  escapes 0
  bytes-K4096.xp     entries  1325  tokens   65472  complete   87984 B  payload   77422 B  escapes 0
  chars-K256         entries   171  tokens  259706  complete  166527 B  payload  166004 B  escapes 0
  chars-K4096        entries   171  tokens  259706  complete  166527 B  payload  166004 B  escapes 0
  freq-K256          entries   255  tokens  175254  complete  145718 B  payload  144712 B  escapes 0
  freq-K256.xp       entries   237  tokens  175501  complete  145601 B  payload  144708 B  escapes 0
  freq-K4096         entries  4095  tokens   81999  complete  130775 B  payload   96761 B  escapes 0
  freq-K4096.xp      entries  1324  tokens   82638  complete  104364 B  payload   96327 B  escapes 0
  length-K256        entries   255  tokens  180224  complete  139799 B  payload  138486 B  escapes 0
  length-K256.xp     entries   227  tokens  180421  complete  139542 B  payload  138500 B  escapes 0
  length-K4096       entries  4095  tokens  101139  complete  148828 B  payload  102829 B  escapes 0
  length-K4096.xp    entries   952  tokens  101672  complete  110648 B  payload  102481 B  escapes 0
  token-K256         entries   255  tokens  135200  complete  116952 B  payload  115785 B  escapes 0
  token-K4096        entries  4095  tokens   39336  complete  101118 B  payload   53049 B  escapes 0
  token-K4096.xp     entries  2135  tokens   58326  complete   92089 B  payload   72768 B  escapes 0
  zstd-19 per file, trained 8 KiB dictionary: complete 89445 B
  zstd-19 per file, no dictionary: complete 126036 B
  zstd-19 one stream, no dictionary: complete 62692 B
  zstd-19 one stream, trained 8 KiB dictionary: complete 70695 B
```

```
dev: 400 files, 270994 bytes, 20 headers, 10.8s
  bpe-K256           entries   255  tokens  163844  complete  141108 B  payload  140162 B  escapes 0
  bpe-K256.xp        entries   246  tokens  164081  complete  141066 B  payload  140163 B  escapes 0
  bpe-K4096          entries  4095  tokens   61922  complete  114290 B  payload   82795 B  escapes 0
  bpe-K4096.xp       entries  2894  tokens   64586  complete  106111 B  payload   83507 B  escapes 0
  bytes-K256         entries   255  tokens  144402  complete  123777 B  payload  122610 B  escapes 0
  bytes-K4096        entries  1579  tokens   73372  complete  100148 B  payload   86198 B  escapes 0
  bytes-K4096.xp     entries  1325  tokens   73909  complete   96708 B  payload   86146 B  escapes 0
  chars-K256         entries   171  tokens  270994  complete  173837 B  payload  173314 B  escapes 0
  chars-K4096        entries   171  tokens  270994  complete  173837 B  payload  173314 B  escapes 0
  freq-K256          entries   255  tokens  185964  complete  153714 B  payload  152708 B  escapes 0
  freq-K256.xp       entries   237  tokens  186218  complete  153596 B  payload  152703 B  escapes 0
  freq-K4096         entries  4095  tokens   88087  complete  138105 B  payload  104091 B  escapes 0
  freq-K4096.xp      entries  1324  tokens   89320  complete  111796 B  payload  103759 B  escapes 0
  length-K256        entries   255  tokens  189115  complete  145805 B  payload  144492 B  escapes 0
  length-K256.xp     entries   227  tokens  189246  complete  145538 B  payload  144496 B  escapes 0
  length-K4096       entries  4095  tokens  108901  complete  155865 B  payload  109866 B  escapes 0
  length-K4096.xp    entries   952  tokens  109926  complete  117797 B  payload  109630 B  escapes 0
  token-K256         entries   255  tokens  144402  complete  123777 B  payload  122610 B  escapes 0
  token-K4096        entries  4095  tokens   65886  complete  133046 B  payload   84977 B  escapes 0
  token-K4096.xp     entries  2135  tokens   67972  complete  102332 B  payload   83011 B  escapes 0
  zstd-19 per file, trained 8 KiB dictionary: complete 93822 B
  zstd-19 per file, no dictionary: complete 130825 B
  zstd-19 one stream, no dictionary: complete 63323 B
  zstd-19 one stream, trained 8 KiB dictionary: complete 72699 B
```

```
fresh: 400 files, 255472 bytes, 20 headers, 10.0s
  bpe-K256           entries   255  tokens  154803  complete  133883 B  payload  132937 B  escapes 0
  bpe-K256.xp        entries   246  tokens  155077  complete  133842 B  payload  132939 B  escapes 0
  bpe-K4096          entries  4095  tokens   58803  complete  110058 B  payload   78563 B  escapes 0
  bpe-K4096.xp       entries  2894  tokens   60854  complete  101545 B  payload   78941 B  escapes 0
  bytes-K256         entries   255  tokens  135694  complete  117106 B  payload  115939 B  escapes 0
  bytes-K4096        entries  1579  tokens   69685  complete   95774 B  payload   81824 B  escapes 0
  bytes-K4096.xp     entries  1325  tokens   70306  complete   92465 B  payload   81903 B  escapes 0
  chars-K256         entries   171  tokens  255472  complete  164428 B  payload  163905 B  escapes 0
  chars-K4096        entries   171  tokens  255472  complete  164428 B  payload  163905 B  escapes 0
  freq-K256          entries   255  tokens  174769  complete  145374 B  payload  144368 B  escapes 0
  freq-K256.xp       entries   237  tokens  174983  complete  145258 B  payload  144365 B  escapes 0
  freq-K4096         entries  4095  tokens   83349  complete  132632 B  payload   98618 B  escapes 0
  freq-K4096.xp      entries  1324  tokens   84577  complete  106380 B  payload   98343 B  escapes 0
  length-K256        entries   255  tokens  178217  complete  138361 B  payload  137048 B  escapes 0
  length-K256.xp     entries   227  tokens  178408  complete  138110 B  payload  137068 B  escapes 0
  length-K4096       entries  4095  tokens  101894  complete  149689 B  payload  103690 B  escapes 0
  length-K4096.xp    entries   952  tokens  102811  complete  111670 B  payload  103503 B  escapes 0
  token-K256         entries   255  tokens  135694  complete  117106 B  payload  115939 B  escapes 0
  token-K4096        entries  4095  tokens   63359  complete  129887 B  payload   81818 B  escapes 0
  token-K4096.xp     entries  2135  tokens   65066  complete   98643 B  payload   79322 B  escapes 0
  zstd-19 per file, trained 8 KiB dictionary: complete 90271 B
  zstd-19 per file, no dictionary: complete 126355 B
  zstd-19 one stream, no dictionary: complete 60841 B
  zstd-19 one stream, trained 8 KiB dictionary: complete 70229 B
```

```
project: 120 files, 176742 bytes, 20 headers, 7.7s
  bpe-K256           entries   255  tokens  118459  complete  100355 B  payload   99410 B  escapes 0
  bpe-K256.xp        entries   246  tokens  118997  complete  100322 B  payload   99420 B  escapes 0
  bpe-K4096          entries  4095  tokens   67749  complete  124603 B  payload   93109 B  escapes 0
  bpe-K4096.xp       entries  2894  tokens   73115  complete  114678 B  payload   92075 B  escapes 0
  bytes-K256         entries   255  tokens  124517  complete  100634 B  payload   99468 B  escapes 0
  bytes-K4096        entries  1579  tokens   84880  complete  110877 B  payload   96928 B  escapes 0
  bytes-K4096.xp     entries  1325  tokens   85258  complete  105406 B  payload   94845 B  escapes 0
  chars-K256         entries   171  tokens  176742  complete  112761 B  payload  112239 B  escapes 0
  chars-K4096        entries   171  tokens  176742  complete  112761 B  payload  112239 B  escapes 0
  freq-K256          entries   255  tokens  128247  complete  104284 B  payload  103279 B  escapes 0
  freq-K256.xp       entries   237  tokens  128902  complete  104181 B  payload  103289 B  escapes 0
  freq-K4096         entries  4095  tokens   72041  complete  125187 B  payload   91174 B  escapes 0
  freq-K4096.xp      entries  1324  tokens   76477  complete  100607 B  payload   92571 B  escapes 0
  length-K256        entries   255  tokens  135819  complete  102048 B  payload  100736 B  escapes 0
  length-K256.xp     entries   227  tokens  136171  complete  101784 B  payload  100743 B  escapes 0
  length-K4096       entries  4095  tokens   95731  complete  141297 B  payload   95299 B  escapes 0
  length-K4096.xp    entries   952  tokens   98313  complete  103846 B  payload   95680 B  escapes 0
  token-K256         entries   255  tokens  124517  complete  100634 B  payload   99468 B  escapes 0
  token-K4096        entries  4095  tokens   81208  complete  153687 B  payload  105619 B  escapes 0
  token-K4096.xp     entries  2135  tokens   82416  complete  114240 B  payload   94920 B  escapes 0
  zstd-19 per file, trained 8 KiB dictionary: complete 60631 B
  zstd-19 per file, no dictionary: complete 57641 B
  zstd-19 one stream, no dictionary: complete 27680 B
  zstd-19 one stream, trained 8 KiB dictionary: complete 36486 B
```

Each run wrote `out/results-<set>.json`, `out/entries-<set>.json`, `out/per-file-<set>.csv` and 20 archives
under `out/archives/<set>/`.

### Step 7. Independent decoder (14:09:21 to 14:09:24)

`independent_decode.py` was written on the workstation from `FORMAT.md` alone, Python 3 standard library
only, and copied to `EXP` with rsync at 14:09:20. It was written once and not edited after its first run
(SHA-256 `1d0a314dfc82606257d94e2b19a412cfc7ad5f528c6df53041f23a1dacca052d`).

What the scorer had looked at before writing it, besides `FORMAT.md`: a directory listing of `out/` and of the
archives with their sizes; the key names of the four set manifests with their first two file rows; the key
names of the four `out/results-*.json` files; and, for each set, the `bpe-K256` row of `headers` printed with
its scalar values. The console output of step 6 was read after the decoder had run.

Commands, run from `EXP` in this order, each exit status 0:

| Command | Start | End |
| --- | --- | --- |
| `python3 -I independent_decode.py --set frozen/sets/train.json --root .. --out out` | 14:09:21 | 14:09:21 |
| `python3 -I independent_decode.py --set frozen/sets/dev.json --root .. --out out` | 14:09:21 | 14:09:22 |
| `python3 -I independent_decode.py --set sets/fresh.json --root . --out out` | 14:09:22 | 14:09:23 |
| `python3 -I independent_decode.py --set sets/project.json --root . --out out` | 14:09:23 | 14:09:24 |

Each wrote `out/decode-<set>.json`.

### Step 8. Bring files back (14:10:34 to 14:10:37)

Run on the workstation, in `REPO/projects/algorithm_solver/literals/objective-holdout-v1`:

```
mkdir -p out sets corpus
rsync -a --include='results-*.json' --include='entries-*.json' --include='per-file-*.csv' --include='decode-*.json' --exclude='*' HOST:EXP/out/ out/
rsync -a HOST:EXP/sets/fresh.json HOST:EXP/sets/project.json sets/
rsync -a HOST:EXP/corpus/ corpus/
rsync -a HOST:EXP/independent_decode.py independent_decode.py
```

All exit status 0. Brought back: 16 files in `out/`, 2 in `sets/`, 520 in `corpus/` (400 in
`corpus/codenet-fresh/`, 120 in `corpus/project/`), and `independent_decode.py`. The archives and the work
directory were not brought back.

A SHA-256 over the sorted per-file SHA-256 list of those 539 files gave the same value on both machines:
`3a4f9ceb18423b4a649ddee886f15d87016a7f5d4358954a4476903fdc3bc671`.

Before the copy, the files in `out/` (other than archives), `sets/`, `corpus/` and `independent_decode.py`
were searched on the scoring host for its host name, its home directory path and the data directory name.
No file matched.

## Outcome of each check

| Check | Outcome |
| --- | --- |
| Frozen checksums, first run on the export of `9d7d54b9e` | FAIL: 33 of 34 OK, `frozen/train.log` missing |
| Frozen checksums, second run after exporting `frozen/train.log` from `b82e3a89b` | PASS: 34 of 34 OK |
| IBM Python near-duplicate cluster file SHA-256 | equal to the given value |
| "ranks 0..399 reproduce the frozen manifest exactly" | printed; `selection.ranks_0_399_reproduce_frozen_manifest` is `true` |
| Decode check, `train` | PASS: 20 archives |
| Decode check, `dev` | PASS: 20 archives |
| Decode check, `fresh` | PASS: 20 archives |
| Decode check, `project` | PASS: 20 archives |

Decode check detail, the same for all four sets (from `out/decode-<set>.json`):

- Archives decoded: 20 of 20, no decode error. The 20 archive names, the 20 `headers` rows in
  `out/results-<set>.json` and the 20 files `frozen/*.boh` are the same set of names.
- Files: every archive holds as many files as the manifest lists (400, 400, 400, 120), and every decoded file
  equals its source file byte for byte, in manifest order. Every source file on disk has the SHA-256 and size
  its manifest row gives.
- Every archive begins with exactly the bytes of `frozen/<name>.boh`.
- Archive size equals `headers[name].bytes.complete`: 20 of 20.
- Tokens decoded equal `headers[name].bit_parse_tokens`: 20 of 20.
- Escapes decoded equal `headers[name].escapes_in_bit_parse`: 20 of 20.
- Entry count equals `headers[name].entries`: 20 of 20.

Recorded in `out/decode-<set>.json` in addition to what was asked, for all 80 archives: the length of
`frozen/<name>.boh` equals the length of magic, entry count, dictionary and code table as parsed; the bits
after the last end-of-file code number at most 7 and are all zero. Checked separately from the two JSON files:
the SHA-256 the decoder computed for each archive equals `headers[name].archive_sha256`, 80 of 80.

## The fresh set (`sets/fresh.json`)

- 200 problems, 400 files (200 Python, 200 JavaScript), 255,472 bytes (Python 91,042; JavaScript 164,430).
- `first_rank` 400, `last_rank` 600. 201 ranks were examined and 200 taken.
- `eligible_overlap_problems`: 1757.
- Skipped: 1 problem.

| Rank | Problem | Reason as recorded |
| --- | --- | --- |
| 562 | `p03356` | identical-problem cluster of a prior or fresh problem |

- No problem was skipped for an exact or whitespace-stripped duplicate file, and none for a Python
  near-duplicate cluster.
- `javascript_near_duplicate_clusters`: "not published by IBM".
- `closest_training_file_shingle_jaccard`:

| Language | Median | p95 | Max | Files at or above 0.8 |
| --- | --- | --- | --- | --- |
| Python | 0.1151 | 0.2483 | 0.3544 | 0 |
| JavaScript | 0.2454 | 0.5436 | 0.6755 | 0 |

- Source as recorded: IBM Project CodeNet v1.0.0 (CDLA-Permissive-2.0), mirror `iNeil77/CodeNet` at
  `1e28cfa9f8eb2df763ad2514af11afd6e92dd07a`.

## The project (`sets/project.json`)

- Selected: `expressjs/express` at commit `1faf228935aa0a13111f92c28ee795be64ce3f0f` (4.21.2), licence MIT.
- Why, as recorded: `candidate_order` is express, TheAlgorithms/Python, requests, ramda, click, underscore.
  `tried` holds one entry, `expressjs/express`, with 120 eligible files. The rule takes the first candidate with
  at least 100 eligible files, so no other repository was downloaded.
- Tarball SHA-256 as recorded: `c9999a37b51e814ea0c0180b0075a7b8a25cda34e24b37641a6acffcf049d453`.
- Eligible files 120, kept 120, `dropped_as_duplicates` empty, 176,742 bytes, all JavaScript. Unit: source file.

## What did not go as written

1. **Step 2 failed on its first run.** `frozen/train.log` is listed in `SHA256SUMS-FROZEN` and was not in
   freeze commit `9d7d54b9e`. The scorer stopped and reported. The trainer side committed the file in
   `b82e3a89b` and recorded the deviation in `DEVIATIONS.md`; the scorer exported that file and
   `DEVIATIONS.md` from `b82e3a89b`, and the full check then passed. So the tree that was scored is
   `9d7d54b9e` plus those two files from `b82e3a89b`.
2. **The export command for those two files was not run exactly as the coordinator wrote it.** As written it
   ended in `</dev/null` after the ssh command. That redirection would have replaced the piped archive as the
   standard input of ssh, so the scorer ran it without `</dev/null`, as in step 1.
3. **Step 4 printed two `RuntimeWarning` lines** from Python's `site` module about `sys.prefix` and
   `sys.exec_prefix`, because the interpreter was started through the relative path `../../venv/bin/python`.
   The script ran to the end with exit status 0.
4. **Run wrappers.** Steps 4, 5, 6 and 7 were started detached, wrapped in `nohup sh -c` so that a start
   time, an end time and the exit status went to a log file under `S/logs/`. The four scoring commands ran
   from one wrapper, one after another, in the order given. The frozen command lines themselves were
   unchanged.
5. **Step 4 took 18 seconds**, not several minutes.
6. **The `tokens` column printed by `score.py` is `headers[name].min_tokens`** in all 80 rows. The decode
   comparison used `headers[name].bit_parse_tokens`, as the scorer was told to. The two fields differ in most
   rows, so the token counts in `out/decode-<set>.json` differ from the printed column in most rows.
7. **No archive contains an escape.** `escapes_in_bit_parse` and the decoded escape count are 0 in all 80
   archives. The escape branch of `independent_decode.py` was therefore not exercised by any archive in this
   run.
8. **`chars-K256` and `chars-K4096` are the same header** (same SHA-256 in `SHA256SUMS-FROZEN`), and
   `bytes-K256` and `token-K256` are the same header. Their archives are byte-identical within each set.
9. The scorer did not write or edit `DEVIATIONS.md`. The copy in `S` is the one committed in `b82e3a89b`.

Nothing else differed from the steps as given. No frozen script failed.

## SHA-256 of the files brought back

```
483dff7418944f0323cf439ef9eab6fc5cafd7e84b3e1230073e3c067ecbc43d  out/results-train.json
23a124c370cbd9a6882049276ec65f64c28b277a1e90259311c6cfb610fe64fd  out/results-dev.json
489cab71f6d1c18f3f53ab504ebd9503610c11a4ab43ead694547f38c35d9b01  out/results-fresh.json
5970a6410a438b698d4ec0220f870c4b50c114c389cbfc0fdd5ff21a8789d989  out/results-project.json
616c86c166a36e722abbe31df4df67ddad5832e7f9b57530c5fdad3dc2a899f7  out/decode-train.json
fac0d4fca5a4f9c2a6509625b71af625a085a3a6faa16d342ef95fc4cf16bc14  out/decode-dev.json
a6860eb518a8bba1417b8de112d1f0d5dec45d81dc0f69bac74725d83e3d9c64  out/decode-fresh.json
004fd009a8cb08028e5487f58baf27a4aa0c777f4f0b1779a45b06b26c5c2886  out/decode-project.json
fd67942c4a9d354973431f9091ad3b7355d9b73cf42f2fce87798de023fe9729  out/entries-train.json
ffa6b46981575cedb9ad265618934fdb725b7f4a4a6ed2d055a927a69168e30a  out/entries-dev.json
ee281a72f98866d37c5866b39a0a7e51062a63f998538cbb01cbaaa281a2e354  out/entries-fresh.json
4524f0ce842e2cdda18d6751315c7042e7e509720e4629ee48480593e0070186  out/entries-project.json
a641b78f93a6d95672eccb529b9341c07af60d84e8cba1aee499cdfbd612ebd3  out/per-file-train.csv
7740314b87c769829e1787e5a8a700bc4066e6aefeae2d385f2813d9ff7adfbe  out/per-file-dev.csv
543781e546607ba9df731be2536b9ff6e0fddc60a7b8292eaf7a9935fccc4fba  out/per-file-fresh.csv
56d95f4adacd978f7d942da3c203188d2a198bd60c44c1f017f474785c2d617d  out/per-file-project.csv
350076b9ccf7d0a904276e3fc30b3befa043ac26553c2d32443ee59bebf8f30d  sets/fresh.json
5fc6b23a89118beb0fbb394e5748cd5874e1be1a7027f40305be636681daa69f  sets/project.json
1d0a314dfc82606257d94e2b19a412cfc7ad5f528c6df53041f23a1dacca052d  independent_decode.py
```
