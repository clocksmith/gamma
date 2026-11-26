# Preregistration: which selection objective survives on unseen code (`objective-holdout-v1`)

**Status:** written before any dictionary in this folder was trained and before any test file was fetched.
The commit that adds this file is the first freeze. A second commit freezes the dictionaries, code tables and
commands. Only after that does the scorer fetch test files.

## Question

A vocabulary can be chosen to spell a corpus with the fewest entries, to use the fewest tokens, or to make the
smallest complete archive. Earlier results suggest these three choices disagree. Every earlier token and byte
comparison between selection rules was scored on the files the rule was trained on. This experiment asks one
thing: **when five selection rules are trained on the same files and frozen, which one uses fewer tokens, and
which one makes smaller archives, on files none of them has seen?**

It does not look for a best dictionary. Every dictionary here comes from a heuristic search. A minimum-token
count below is the exact minimum for a given dictionary, never a claim that the dictionary is optimal.

## What is already known (development evidence)

These numbers were measured before this file was written. They are background. None is a result of this
experiment.

- Training files: CodeNet `primary`, 200 problems, 400 files, 259,706 bytes
  ([`../codenet-replication-v1`](../codenet-replication-v1/README.md)). The same folder's `secondary` split (200
  other problems, 400 files, 270,994 bytes) is **development data** here. It has been scored before, and
  dictionaries have been searched on it.
- On `primary`, in sample, the token-gain order at 4,096 entries used 39,331 tokens against 50,431 for BPE, and
  its complete archive was 101,497 bytes against 86,127 for a 1,600-entry prefix of the same order.
- On `secondary`, a dictionary trained on `primary` lost to zstd with a trained dictionary: 98,575 bytes at
  best with tables fixed on training (96,312 with tables refitted on the test files) against 93,822. That
  comparison counted zstd as 400 separately decodable files with boundaries kept outside the archive, and
  BITS as one stream. It also let the BITS side add single-byte entries after reading the test files (none
  were needed).
- **Found while fixing the sample rule below:** IBM's list of identical problems puts two `primary` problems
  in the same cluster as two `secondary` problems (`p03197` with `p03195`, `p03419` with `p03417`). So 2 of the
  200 `secondary` problems are copies of training problems. Two further clusters lie inside `secondary`. The
  earlier split did not consult that list.

## Data

| Set | Role | Who reads it |
| --- | --- | --- |
| `train` | CodeNet `primary`. The only input to every dictionary, code table and the zstd dictionary | trainer |
| `dev` | CodeNet `secondary`. Scored and reported as development evidence only | trainer and scorer |
| `fresh` | 200 new CodeNet problems, one Python and one JavaScript file each | scorer only |
| `project` | one untouched repository | scorer only |

**`fresh`.** [`select_fresh_codenet.py`](select_fresh_codenet.py) is the rule. It is the earlier rule (accepted
submissions, Python 3 and JavaScript, valid UTF-8, no NUL byte, 64 to 4,096 bytes, problems ordered by
SHA-256 of a fixed prefix plus the problem id, lower-median submission by length) continued from rank 400. It
must first reproduce all 800 `primary` and `secondary` files exactly, or it stops. A problem is skipped, and
the next rank taken, when:

1. it is in the same IBM identical-problem cluster as a `primary` or `secondary` problem, or as a fresh problem
   already taken ([`metadata/ibm-identical-problem-clusters.txt`](metadata/ibm-identical-problem-clusters.txt),
   153 clusters, SHA-256 `d4731781…3520`, from `derived/duplicates/` of the IBM archive);
2. its Python or JavaScript file equals an earlier file exactly, or after all whitespace is removed;
3. its Python submission shares an IBM near-duplicate cluster with a `primary` or `secondary` Python
   submission. IBM publishes near-duplicate clusters for Python, C, C++ and Java, not JavaScript.

Each skip is recorded with its reason. The script also reports, without acting on it, how close each fresh
file is to its nearest training file (shared 8-byte substrings).

**`project`.** [`select_project.py`](select_project.py) is the rule. Six repositories that no BITS experiment
has used were pinned to a commit and ordered by a hash of their names before any was downloaded: express,
TheAlgorithms/Python, requests, ramda, click, underscore, in that order. The first with at least 100 eligible
files is the project. Eligible means the same size and encoding rule as CodeNet. At most 200 files are kept,
chosen by a hash of the path.

**Unit of comparison.** One CodeNet problem (its two files together), or one project file.

## Arms

All arms see the same 400 training files. All may use any string of 2 to 16 bytes that occurs inside one
training file. All get the same single-byte entries: every byte value that occurs in training (a train-only
set; 171 values). All get the same escape. The cap counts every single-byte entry, the escape and every
fragment, so a cap of `K` leaves `K - 172` fragment slots: **84 at 256 and 3,924 at 4,096**.

| Arm | Rule for choosing fragments | Search limit |
| --- | --- | --- |
| `bpe` | Byte-pair merges in order of pair count, merged strings up to 16 bytes | none needed |
| `freq` | Most overlapping occurrences first; ties by more files, then shorter, then bytewise | none needed |
| `length` | Negative control. Non-overlapping occurrences times (length minus 1), largest first | none needed |
| `token` | Greedy by the exact drop in training tokens after reparsing | 300 s |
| `bytes` | The prefix of the `token` order, or of the gain-per-stored-byte order, whose complete training archive is smallest | 300 s per order |
| `chars` | Reference only: single bytes and the escape, no fragments | none |

`bpe`, `length`, `token` and the gain-per-stored-byte order come from the unmodified engine
[`../fixed-source-v3/engine.c`](../fixed-source-v3/engine.c) (modes `bpe`, `freq-occ`, `greedy-entry`,
`greedy-byte`; policy `s1-whole`; 16-byte limit; 4,096 entries). `freq` and the `bytes` choice are in
[`train_arms.py`](train_arms.py). For `bytes`, prefixes are tried every 16 entries at the 256 cap and every 64
at the 4,096 cap; the three best of each order by a quick count are refitted in full and the smallest wins.
`bytes` may therefore stop below the cap. Realized entries are reported beside every cap.

`length` is not a contender. It is there to show what preferring long entries costs when nothing charges for
their stored bytes or checks that they still get used after overlap.

`bytes` judges whole prefixes by recounting the whole archive. It does not test fragments one at a time. The
ablation below does that, as a measurement, not as an arm.

## Format and accounting

[`FORMAT.md`](FORMAT.md) defines the archive. Counted: magic and counts, dictionary, code table, payload. One
shared table, so no routing. The escape takes a slot and each escaped byte costs the escape code plus eight
bits. No byte value and no code length is learned from a test file.

The **code table** is fitted on training files only ([`bits_oh.py`](bits_oh.py), `fit_table`): start from the
minimum-token parse, give every entry and the escape a count of at least one, then reparse for minimum bits
and refit while the training payload strictly shrinks, at most 15 passes.

Two access contracts are reported and never mixed. **Sequential** (the headline): one archive, read front to
back, boundaries inside it. **Random access**: each file padded to a byte plus a one-varint index entry per
file, charged to BITS and zstd alike.

## Scoring

[`score.py`](score.py) is the frozen command. For each frozen header and each set it reports:

- **Tokens:** the exact minimum number of tokens for that dictionary; an escaped byte is one token.
- **Bytes:** the size of the real archive, encoded with the frozen table and a minimum-bit parse for those
  fixed code lengths. Split into dictionary, table, counts and payload, and also the figure when the
  dictionary is already held.
- **Per file:** source bytes, tokens, distinct entries used, escapes; per set, the lengths of the entries
  actually used.
- **Matches against uses:** overlapping matches of fragments in the text, against uses in the chosen parse.
- **Reuse:** each fragment's uses split into repeats inside one file, a second file of the same unit, and
  first use in a unit.
- **Paired:** for the arm pairs listed in `score.py`, units where one arm is lower, higher or tied, with a
  two-sided sign test.
- **zstd 1.5.7, level 19:** one frame per file with the 8 KiB dictionary trained on `train` (the earlier
  winner), and three further rows for context.

A separately written decoder must reproduce every file from every archive byte for byte, or the run fails.

## One ablation: does each fragment pay its rent?

For every fragment of every arm, `score.py` removes it, reparses the files that used it with the code lengths
unchanged, and recounts complete bytes. The fragment **pays rent** on a set if the payload grows by more than
the header bytes it frees (its length plus two). This is measured on `train`, `fresh` and `project`, and
grouped by how many training problems used the fragment (0, 1, 2 to 3, 4 or more).

One group removal is trained as well: each arm with every fragment dropped that fewer than two training
problems used, and its table refitted on training files (headers named `*.xp`). It uses training data only.

## Decision rules

A difference under 1.0% is treated as no difference, as in the earlier CodeNet protocol. `fresh` decides.
`project` is reported beside it and never pooled with it.

| Id | Statement | Holds if |
| --- | --- | --- |
| **T** | Token savings transfer | On `fresh`, at both caps, `token` uses at least 1.0% fewer tokens than `bpe`, and is lower on more problems than it is higher (sign test, p < 0.05) |
| **B** | The byte objective wins archives | On `fresh` at the 4,096 cap, the `bytes` archive is at least 1.0% smaller than the `token` archive. At 256 the two rules may pick the same dictionary; that is reported, not counted |
| **C** | The negative control behaves as one | On `fresh` at both caps, `length` uses more tokens and makes a larger archive than `token` |
| **R** | Reuse predicts rent | On `fresh` at the 4,096 cap, for `token`, the share of fragments that pay rent is higher for those used by 4 or more training problems than for those used by one |
| **X** | Single-problem fragments cost bytes | On `fresh` at the 4,096 cap, `token.xp` makes an archive at least 1.0% smaller than `token` |
| **Z** | BITS beats trained zstd | The best BITS arm is at least 1.0% smaller than zstd with the trained dictionary on `fresh` and on `project`, under the same access contract. Expected to fail |

How the headline follows:

- T and B hold: the objectives diverge on unseen code. That is the paper.
- T fails: the token advantage was an in-sample effect. The paper says where reuse fails.
- T holds and B fails: token selection is enough on unseen code at this size; the archive penalty was specific
  to the training files or to the header charge. Say so.
- Z holding would need its baselines, costs and workloads stated; nothing else here claims a better codec.

## Scorer and order of work

1. This file, the scripts and the format are committed and pushed. Nothing is trained yet.
2. The trainer runs `train_arms.py`, which reads `train` only, and commits `frozen/` with `SHA256SUMS-FROZEN`.
3. The scorer is a separate agent session started after step 2. It takes no part in steps 1 and 2. It alone
   fetches `fresh` and `project`, on a machine other than the trainer's working copy, runs the frozen commands
   unchanged, and writes its own decoder from `FORMAT.md` without reading `bits_oh.py`.
4. The trainer does not change any frozen file after step 2. If a frozen script fails to run, the fix and the
   reason are recorded in `DEVIATIONS.md` before any result is read.

The scorer is a second session of the same assistant under the same owner. That keeps the trainer away from
the test files; it is not review by an uninvolved person. Before anything is posted, someone uninvolved still
has to check the splits, the accounting, the decode and the wording.

## What the trainer has seen of the test side

The identical-problem cluster file; the first lines of IBM's Python near-duplicate file, to learn its format;
the names, licences and commit hashes of the six candidate repositories. No fresh CodeNet file and no file of
any candidate repository.

## Not part of this experiment

No sweep over cohort size, similarity or entry length. No tuning after test results. The sealed short-record
codec test stays separate and closed. Deco #127 stays paused and its open checks stay open. Nothing here
authorizes posting or submitting a paper.
