# Fresh short-record workloads (`fresh-short-records-v1`)

Three new short-record workloads for the BITS decision gate, built on
2026-11-25 by a custodian who is not the codec's author.

The earlier short suites (`../rung2-short-ra-bench-v1/`) held out 160 records
that came from the same repositories as the training records, and those
held-out sets were then used while the codec was designed. They no longer count
as a test. These workloads replace them:

- the split is by source project, never by record;
- the test records and the names of the test sources are held outside the
  repository until the codec is frozen;
- this directory, with the test-file hashes, is meant to be committed before
  anything is scored.

This directory holds no third-party record content: only rules, source names,
commit hashes, counts and hashes.

## Files

| File | Content |
|---|---|
| `README.md` | This description. |
| `manifest.json` | Rules per workload; train and validation sources with pinned commits, licence, counts; for the test split only counts, length statistics and hashes. |
| `build_corpus.py` | The builder. It reads the source list and the salt from the custody directory, so the script alone does not reveal the test sources. |

## Workloads

| | Record | Source unit | Record length |
|---|---|---|---|
| `w1-short-files` | The whole content of one small source or config file | repository | 40 to 400 bytes |
| `w2-message-entries` | One entry of an English message catalogue | project | 40 to 1,024 bytes |
| `w3-commit-subjects` | The subject line of one non-merge commit | repository | 40 to 1,024 bytes |

**W1** takes files with these extensions: `.json .yml .yaml .toml .ts .tsx .js
.jsx .mjs .cjs .wgsl .glsl .vert .frag .css`. Files under directories that
usually hold copied or generated code are skipped (`node_modules`, `vendor`,
`third_party`, `dist`, `build` and similar; the full list is in the manifest).
This is the regime of the earlier short suites (whole files of about 150
bytes), with data from unrelated repositories.

**W2** takes the project's own English catalogue files. A JSON catalogue gives
one record per string value, written as `"key": "value"` with nested keys
joined by a dot. Line formats (`.properties`, `.ini`, `.ftl`, `.strings`, PHP
string tables) give the stripped `key = value` line. Android resources give the
stripped `<string name="...">...</string>` line. At most 40 catalogue files are
read per project.

**W3** takes the commits reachable from the pinned commit inside a time window.
The window is the first of 10, 45, 180, 730 or 2,920 days that holds at least
700 non-merge commits. Merge commits are left out.

Rules shared by all three:

- A record must be valid UTF-8 with no NUL byte and within the length range.
- Each source keeps one copy of a record. A record found in several sources is
  kept in one of them only (the one with the smallest
  `sha256(source name + 0x00 + record)`).
- A source is used only if it has at least 200 distinct eligible records.
- Each source contributes at most 150 records: the ones with the smallest
  `sha256(salt + record)`. In this build every source reached 150, so all
  sources have equal weight.

The 40-byte floor applies to all three workloads. For W2 and W3 this removes
the shortest entries and subjects, so those two are not the full natural length
distribution of catalogues and commit logs.

## How sources were chosen

The custodian listed 460 public projects by hand before any salt existed, each
under a different owner account. A candidate was dropped when:

- no open licence was recognised in the licence files at the repository root,
  or those files also carried commercial or source-available terms (21 dropped);
- it had fewer than 200 distinct eligible records (46 dropped);
- no English catalogue in a supported format was found (4 dropped, W2 only);
- it belonged to the same organisation as another source (11 dropped);
- it shared 5% or more of its eligible records with another source, which
  means one copies the other; the larger of the two was dropped (3 dropped,
  for example a tool that carries another project's test fixtures).

That left 76, 131 and 168 sources. The reasons are recorded per candidate in
the custody directory.

Excluded from the start:

- everything under the repository owner's GitHub account (`clocksmith`). The
  earlier short suites were sampled from local checkouts of that account's
  repositories, as `run_ra_pareto_bench.py` shows;
- projects those repositories vendor or build on: Dawn and other
  Google-run accounts, the WebGPU specification group, three.js, and the
  browser machine-learning libraries;
- third-party repositories the lane already used elsewhere (the LeetCode
  collections, Project CodeNet, FSST, CPython and the few others named in the
  lane's attribution files).

"Organisation" means the owner account, plus a judgement by the custodian
where one company or foundation team runs several accounts. No organisation
appears twice anywhere, so no project is shared between two workloads either.
Projects that only share a foundation umbrella (for example two unrelated
projects of the same software foundation under different accounts) count as
separate organisations.

## Split

Splits are assigned per workload:

1. Sort the sources by `sha256(salt + source name)`.
2. The last quarter (rounded up) is the test split, the quarter before it
   (rounded up) is validation, the rest is train.

The salt is 32 random bytes. It was generated once, after the source list was
final, and exists only in the custody directory. The same salt picks each
source's 150 records.

## Result

Built 2026-11-25T13:10:32Z. Lengths are bytes per record.

| Workload | Split | Sources | Records | Total bytes | Min | Median | Mean | p95 | Max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `w1-short-files` | train | 38 | 5,700 | 1,232,922 | 40 | 216 | 216.30 | 380 | 400 |
| | validation | 19 | 2,850 | 548,025 | 40 | 180 | 192.29 | 374 | 400 |
| | test | 19 | 2,850 | 592,814 | 40 | 196 | 208.00 | 378 | 400 |
| `w2-message-entries` | train | 65 | 9,750 | 768,805 | 40 | 62 | 78.85 | 171 | 1,011 |
| | validation | 33 | 4,950 | 395,191 | 40 | 65 | 79.84 | 166 | 957 |
| | test | 33 | 4,950 | 409,487 | 40 | 67 | 82.72 | 176 | 805 |
| `w3-commit-subjects` | train | 84 | 12,600 | 777,820 | 40 | 57 | 61.73 | 92 | 793 |
| | validation | 42 | 6,300 | 374,475 | 40 | 56 | 59.44 | 85 | 459 |
| | test | 42 | 6,300 | 383,434 | 40 | 57 | 60.86 | 89 | 396 |

Test-file hashes (`sha256` of `test.jsonl`):

| Workload | sha256 |
|---|---|
| `w1-short-files` | `a004cc9880aa80077532f4d445f573862d2902341c258990c30aa977acaeb118` |
| `w2-message-entries` | `4f5af669106af4194be64e3564f4345076fdd1d23f58a213ed4eb59f5ab0cb9d` |
| `w3-commit-subjects` | `39d078a8299567989f62a7d72a2f930ee79dd19b38a6acc32567001063b631b3` |

The manifest also carries, per workload,
`sha256(salt + sorted test source names joined by a newline)`. Once the salt is
published, anyone can check the test source list against it.

## Which workloads decide

Use **W1 and W2** for the decision. **W3 is the spare.**

This choice does not depend on any codec result:

- The order was set in the brief before any data was built.
- W1 and W2 have test means inside the 60 to 300 byte target (208.0 and 82.7).
  W3 sits at the lower edge (60.9, median 57).
- W3 has the most machine-written lines: about 3.5% of its released training
  records match a dependency-update pattern.

W3 replaces a decision workload only if that workload's seal is broken or its
build is found to be wrong. A score is never a reason to swap.

## Custody, and its limit

The records live in the custody directory (outside the repository):

- `release/<workload>/train.jsonl` and `validation.jsonl`: the codec author may
  read these.
- `sealed/<workload>/test.jsonl`, the salt, the full source list and the list
  of test sources: not to be read by the codec author before the freeze.

Each line of a record file is a JSON object with `id`, `source` and
`record_b64` (the record bytes in base64).

**This is a promise, not an enforced barrier.** The sealed directory has mode
700, but every session on the machine runs under one account, so nothing stops
a session from opening it. The custodian's own working log sits on the same
machine and is covered by the same promise; the custodian's scratch caches were
deleted after the build. If the promise is broken for a workload, say so and
treat that workload as spent.

The train and validation source lists in the manifest are public. Someone who
knows which well-known projects are missing could guess at test sources, but
cannot confirm a guess without the salt.

## Before scoring

1. Commit this directory.
2. Commit the pass and fail thresholds and the choice of decision workloads.
3. Freeze the codec and record the freeze.
4. Only then let the scorer read `sealed/`. Check each `test.jsonl` against the
   hash above before scoring.

## Rebuild

The builder needs Python 3 (standard library only) and a recent `git` (built
with 2.50). It
fetches anonymously over HTTPS with credential helpers, user configuration and
prompts switched off. Each fetch is shallow and filtered (small blobs only for
W1, named catalogue files for W2, commit objects for W3), and each clone is
deleted as soon as its records are extracted.

A rebuild needs `sealed/salt.hex` and `sealed/sources-full.json` from the
custody directory. They stay sealed until after scoring.

```bash
python3 build_corpus.py extract --custody <custody dir> --work <scratch dir>
python3 build_corpus.py build   --custody <custody dir> --work <scratch dir> \
    --out-custody <output dir>
python3 build_corpus.py verify  --custody <custody dir> --public .
```

`extract` fetches every pinned commit again. `build` writes the record files;
their hashes must equal the ones in `manifest.json`. The first build ran
`pin`, `finalize`, `extract`, `finalize --recheck`, `init-salt` and `build` in
that order.

## Checks run on 2026-11-25

- **Rebuild.** Every pinned commit of all three workloads (389 sources at the
  time) was fetched a second time into an empty cache. The nine record files
  built from the second fetch are byte-identical to the custody files.
- **Splits.** No source is in two splits. No organisation is in two splits or
  in two workloads. The test split equals the salted ranking.
- **Records.** No record is in both a release file and a sealed file. No
  duplicate records inside a workload. Every record passes the length and
  encoding rules. No source exceeds 150 records.
- **Public files.** None of the 94 test source names (`owner/name`), none of
  their pinned commit hashes and none of the 56,250 records (as text or as
  base64) occurs in this directory, and the salt does not either.

`build_corpus.py verify` repeats these checks, except the rebuild.

## Limits

- The sources are well-known public projects picked by hand, all hosted on
  GitHub and all in English. They are not a random sample of public code.
- W1 leans towards the JavaScript and TypeScript ecosystem, infrastructure
  configuration and test fixtures. The file type of each record is not kept.
- The licence check is pattern matching on root licence files. It recognises
  common open licences and rejects anything it cannot place. The `licence`
  field lists every licence name found, which for some repositories includes
  licences of bundled third-party code. Findings per file are in the custody
  copy.
- Commit hashes pin the content, but a rebuild depends on the hosts still
  serving those commits.
