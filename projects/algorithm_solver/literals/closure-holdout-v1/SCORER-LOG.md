# closure-holdout-v1 scorer log

Scorer run for step 2 of "Order of work" in [PREREGISTRATION.md](PREREGISTRATION.md). The scorer is a separate
agent session from the builder (same machine and model family). No committed script, rule or frozen file was
edited. Each script was run once, with the parameters below.

Placeholders: `REPO` is the gamma checkout, `EXP` is `REPO/projects/algorithm_solver/literals/closure-holdout-v1`,
`W` is a new temporary work directory outside the repository. `W` (downloaded parquet and tarballs) was deleted
after scoring and before the commit.

- Run start: 2026-11-26T21:03:31Z
- Run end (scoring finished, `W` deleted): 2026-11-26T21:13:27Z

## Tools

| Tool | Version |
| --- | --- |
| `python3` | Python 3.14.2 |
| `REPO/.venv/bin/python` | Python 3.14.2 |
| pyarrow (venv) | 23.0.0 |
| `shasum` | 6.02 |

## Step 1: freeze check

Commands, from `REPO`:

```text
git fetch origin main
git rev-parse origin/main HEAD
git merge-base --is-ancestor 96423fc63 origin/main
git diff --stat 96423fc63 -- projects/algorithm_solver/literals/closure-holdout-v1
shasum -a 256 frozen/dictionaries.json          (from EXP)
grep -n "^DICTIONARIES_SHA256" score.py         (from EXP)
```

Output:

```text
From github.com:clocksmith/gamma
 * branch                main       -> FETCH_HEAD
fetch exit 0
96423fc635c135326c653990cb08e6e8b44aad7b
96423fc635c135326c653990cb08e6e8b44aad7b
ancestor exit 0
diff exit 0
4f2d4410f6e6a841fbd01783ec9a0f03498f40f356d9f2996642debe0ba543b7  frozen/dictionaries.json
31:DICTIONARIES_SHA256 = '4f2d4410f6e6a841fbd01783ec9a0f03498f40f356d9f2996642debe0ba543b7'  # frozen dictionaries; checked before scoring
```

Result: `origin/main` and local `HEAD` were both 96423fc635c1; 96423fc63 is an ancestor of `origin/main`; the diff
of the experiment folder against 96423fc63 was empty and the working tree was clean. SHA-256 of
`frozen/dictionaries.json`: `4f2d4410f6e6a841fbd01783ec9a0f03498f40f356d9f2996642debe0ba543b7`, equal to the
preregistered value and to `DICTIONARIES_SHA256` in `score.py`. All checks passed.

## Step 2: select fresh2

Command, from `EXP`:

```text
REPO/.venv/bin/python -I select_fresh2.py --work W
```

- Start: 2026-11-26T21:03:59Z
- End: 2026-11-26T21:11:58Z
- Exit status: 0

Complete console output (stdout and stderr):

```text
python shard 0 read, 890 buffered problems
python shard 1 read, 1090 buffered problems
python shard 2 read, 1370 buffered problems
python shard 3 read, 1757 buffered problems
primary, secondary and fresh ranks reproduce
fresh2: 200 problems, 400 files, 243510 bytes, ranks 601..811, skipped 11
```

Downloaded into `W`: `JavaScript_train-00000-of-00001.parquet` (26,977,202 bytes) and
`Python_train-0000{0,1,2,3}-of-00004.parquet` (150,191,423; 152,111,649; 149,199,300; 116,189,318 bytes).

## Step 3: select projects

Command, from `EXP`:

```text
python3 -I select_projects.py --work W
```

- Start: 2026-11-26T21:12:08Z
- End: 2026-11-26T21:12:13Z
- Exit status: 0

Complete console output (stdout and stderr):

```text
project-python: TheAlgorithms/Python at 30507bbe4139, 1045 eligible, 200 kept, 382385 bytes
project-javascript: ramda/ramda at 980b3bf7712a, 660 eligible, 200 kept, 203300 bytes
```

Downloaded into `W`: `TheAlgorithms__Python-30507bbe4139.tar.gz` (8,457,964 bytes) and
`ramda__ramda-980b3bf7712a.tar.gz` (473,296 bytes). Each language took the first candidate tried; no files were
dropped as duplicates (see `sets/project-*.json`).

## Step 4: score

Command, from `EXP`:

```text
python3 -I score.py --out out
```

- Start: 2026-11-26T21:12:18Z
- End: 2026-11-26T21:13:05Z
- Exit status: 0

Complete console output (stdout and stderr):

```text
train: K4096 closed vs token +24.87%, closed vs bpe -2.61%; K256 closed vs token +14.57%, closed vs bpe -0.44%
dev: K4096 closed vs token -7.38%, closed vs bpe -1.45%; K256 closed vs token +13.08%, closed vs bpe -0.34%
fresh: K4096 closed vs token -8.32%, closed vs bpe -1.22%; K256 closed vs token +13.65%, closed vs bpe -0.38%
project: K4096 closed vs token -17.48%, closed vs bpe -1.09%; K256 closed vs token -5.35%, closed vs bpe -0.50%
fresh2: K4096 closed vs token -8.47%, closed vs bpe -1.24%; K256 closed vs token +13.36%, closed vs bpe -0.39%
project-python: K4096 closed vs token -18.29%, closed vs bpe -0.85%; K256 closed vs token -5.95%, closed vs bpe +0.92%
project-javascript: K4096 closed vs token -17.28%, closed vs bpe -1.36%; K256 closed vs token -4.74%, closed vs bpe +0.52%
rules: {"S": true, "O": true, "P": true, "F": true, "G": true, "J-python": true, "J-javascript": true}
```

Outputs: `out/results.json`, `out/per-file.csv`.

## Rule outcomes as printed by score.py

| Rule | Outcome |
| --- | --- |
| S | true |
| O | true |
| P | true |
| F | true |
| G | true |
| J-python | true |
| J-javascript | true |

## Files added by this run

`sets/fresh2.json`, `sets/project-python.json`, `sets/project-javascript.json`, `corpus/codenet-fresh2/`,
`corpus/project-python/`, `corpus/project-javascript/`, `out/results.json`, `out/per-file.csv`, this log and
`NOTICE`.
