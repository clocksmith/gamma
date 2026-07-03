# enwiki9

Lossless compression of `enwik9` — the first 10^9 bytes of the English Wikipedia XML dump (Matt Mahoney / Hutter Prize benchmark).

For a mechanism-level guide to the custom algorithms and their measured status,
see [ALGORITHMS.md](ALGORITHMS.md).

For a plain-English view of what each major algorithm does and how it scored,
see [docs/algorithm_cards.md](docs/algorithm_cards.md).

For the project ownership map, active proof lane, and documentation routing,
see [PROJECT_ORGANIZATION.md](PROJECT_ORGANIZATION.md).

For the current generated operator receipt, see
[docs/status_receipt.md](docs/status_receipt.md).

For artifact-backed rankings from result JSONs only, see
[docs/evidence_matrix.md](docs/evidence_matrix.md).

For a compact generated top-results view by measured scope, see
[docs/best_results.md](docs/best_results.md).

For the active cmix21 PPMD memory-valve ladder, see
[docs/cmix21_memory_valves.md](docs/cmix21_memory_valves.md).

For cached residual/SSE shadow evidence, see
[docs/residual_shadow_matrix.md](docs/residual_shadow_matrix.md).

For the strategy and novel-algorithm research register, see
[docs/research_register.md](docs/research_register.md).

For the primary novel SRSTC / streaming self-referential retrieval strategy
that turns cosine-style similarity into deterministic compressor state, see
[docs/streaming_retrieval_mixer.md](docs/streaming_retrieval_mixer.md).

For handoff/continuation rules during active cmix21 runs, see
[docs/takeover_runbook.md](docs/takeover_runbook.md).

For the FX2-SC sidecar-context implementation roadmap, see
[FX2_SC.md](FX2_SC.md). For the paper-style thesis version, see
[FX2_SC_PAPER.md](FX2_SC_PAPER.md).

Candidate source, metadata, audit, retirement, and PGSG-readiness rules are in
[CANDIDATES.md](CANDIDATES.md). The current generated audit snapshot is
[CANDIDATE_INVENTORY.md](CANDIDATE_INVENTORY.md).

## Layout

```
enwiki9/
├── README.md              this file
├── PROJECT_ORGANIZATION.md ownership map + active proof lane
├── ALGORITHMS.md          custom algorithm mechanisms + benchmark status
├── FX2_SC.md              sidecar-context thesis + rollout plan
├── FX2_SC_PAPER.md        paper-style FX2-SC design thesis
├── CANDIDATES.md          candidate lifecycle + PGSG metadata policy
├── CANDIDATE_INVENTORY.md generated candidate audit snapshot
├── index.json             registry of programs + leaderboard
├── data/
│   ├── enwik9.zip         downloaded archive (~322 MB)
│   └── enwik9             extracted dataset (1,000,000,000 bytes)
├── programs/
│   └── <program_id>/
│       ├── meta.json      program metadata (added, description, deps)
│       └── program.py     exposes compress(bytes)->bytes, decompress(bytes)->bytes
├── lib/
│   └── driver.py          run/verify/score one program
├── tools/                 audit, package, queue, residual, ordering utilities
├── docs/                  algorithm cards, accounting, shadow-coder, reports, and handoff notes
├── results/
│   └── <program_id>/<timestamp>.json   per-run measurements
└── bench.py               run all programs, update leaderboard
```

## Program contract

Every program is a directory under `programs/` with two files:

**`program.py`** — must define:
```python
def compress(data: bytes) -> bytes: ...
def decompress(data: bytes) -> bytes: ...
```

**`meta.json`**:
```json
{
  "id": "baseline_lzma",
  "description": "stdlib lzma at preset=9 | extreme",
  "added": "2026-05-08",
  "deps": []
}
```

The driver loads `programs/<id>/program.py` as a module and runs the roundtrip.

## Score: what `S` and `b/B` mean

The Hutter Prize is scored in **bytes**, not ratio:

```
S := S1 + S2
     S1 = size of the decompressor (program.py + every sibling file the decoder reads)
     S2 = size of the compressed archive
```

`S` is the figure of merit. **Smaller wins.** The current world record is `fx2-cmix` at `S = 110,793,128`. The prize is paid for `S < 109,685,197` on the full 10⁹-byte `enwik9`.

In this repo's results JSONs, `hutter_score` ≡ `S`, `compressed_size` ≡ `S2`, `program_size` ≡ `S1`. The driver counts every file in `programs/<id>/` toward `program_size` *except* `meta.json` and `__pycache__`, so inlined data files (e.g., `cmix_wrapped` ships its binary base64-encoded inside `program.py`) are scored honestly.

`bits_per_byte` (often abbreviated b/B) is a derived diagnostic, not the contest score:

```
bits_per_byte = compressed_size · 8 / data_size
```

It maps to information-theoretic statements (Shannon entropy of natural English is ~0.6–1.3 b/char depending on protocol; `fx2-cmix` achieves ~0.886 b/B on `enwik9`). It is **archive-only** — it does not include `program_size`. A program with great `b/B` and giant decompressor is a bad submission. **`S` is what matters; `b/B` is what we use to talk shop.**

## Interpreting result JSONs

Every run produces `results/<program_id>/<timestamp>.json` with these fields:

| field | meaning |
|---|---|
| `program_id` | matches a directory under `programs/` |
| `data_path` | the corpus or fixture used as input |
| `data_size` | bytes of input fed to `compress()` |
| `data_md5` / `data_sha256` | hashes of input — must match across hosts to compare |
| `compressed_size` | bytes returned by `compress()` |
| `compressed_md5` / `compressed_sha256` | hashes of the archive — for cross-host determinism check |
| `program_size` | sum of bytes of every file in `programs/<id>/` except `meta.json` |
| `program_files` | breakdown of which files contributed to `program_size` |
| `hutter_score` | **S = compressed_size + program_size** — the only number the contest cares about |
| `bits_per_byte` | `compressed_size · 8 / data_size` |
| `compress_time_s` / `decompress_time_s` | wall time per phase |
| `roundtrip_ok` | `decompress(compress(x)) == x`. Binary. **Non-negotiable.** |
| `determinism` | present only if `--check-determinism`; reports byte-equal across two compress calls on this host |
| `host` | machine, OS, python version, hostname — for cross-host comparison |
| `timestamp` | ISO 8601, used in the result filename |

A result is **valid** iff `roundtrip_ok == true` and `data_size + data_md5` are consistent with the corpus you intended to measure. A result without `roundtrip_ok` is not a result; it's a bug report.

## Scope discipline (slice vs. full-corpus)

`enwik9` is **not statistically uniform**. The middle ~300 MB (bytes 400–700 M) is dominated by auto-generated geographic-template articles that compress *much* better than the head of the file. Concrete:

| program | scope | S | b/B | ratio |
|---|---|---:|---:|---:|
| `xz_lzma2_1g` | 100 MB prefix | 24,766,836 | **1.981** | 4.04× |
| `xz_lzma2_1g` | full 10⁹ | 197,822,756 | **1.583** | 5.06× |
| `baseline_lzma` | 1 MB prefix | 290,933 | 2.326 | 3.44× |
| `baseline_lzma` | full 10⁹ | 211,776,421 | 1.694 | 4.72× |

Same compressor. Same source bytes (the prefix is literally the head of the same file). Different `b/B` because shorter prefixes don't include the redundancy-rich middle.

**Rules for honest comparisons:**

1. **Same scope or it's not a comparison.** Comparing `program_A` at 10 MB to `program_B` at 1 GB is meaningless. The driver writes `data_size` into every result; check it before drawing conclusions.
2. **Slice numbers don't predict full-corpus signs.** `schema_lzma_v1` lost on a 1 MB slice (+3,240 bytes vs. baseline) and won on the full corpus (−1,896,296 bytes). The slice had too few `<text>` blocks for the per-block overhead to amortize. Always rerun before claiming a result has scaled.
3. **The contest result is on 10⁹ bytes.** Anything else is diagnostic. Label slice runs as such in any report.
4. **A 100 MB prefix `b/B` is typically 0.3–0.5 b/B *worse* than the full-corpus `b/B` for the same compressor.** Going from prefix to full reliably *improves* compression on this corpus. Surprise wins on a slice should be re-measured.

## Reporting protocol

When reporting a run (in a PR, a comment, a leaderboard update), include:

1. **What** — `program_id`, `data_size` (full corpus or slice), `data_md5` for verification.
2. **Numbers** — `S`, `b/B`, `compressed_size`, `program_size`, `compress_time_s`, `decompress_time_s`.
3. **Determinism** — at minimum, single-host `compressed_sha256`. For a contest claim, two-host SHA256-equal.
4. **Roundtrip** — `roundtrip_ok: true`. Don't report numbers from a run where this is false.
5. **Comparison** — what was beaten (or lost to), at the same scope, with the same `data_md5`. Δ in absolute bytes and as a percent of the comparand.
6. **Provenance** — host info (kernel, libc, libm version where relevant), and the exact command run.

A skeleton report:

```
program: schema_lzma_v1
scope: full 10⁹ bytes
data_md5: 5b8f88a51bb1f6a3aedd0e9a3df8eb1d
S = 209,880,125  (b/B 1.679)
  compressed_size = 209,877,656
  program_size    = 2,469
roundtrip_ok = true
compressed_sha256 = 62563e9d7f12...
determinism: single-host byte-equal across 2 runs
compress_time_s = 1066.7
decompress_time_s = 8.4
host = Linux x86_64, gcc 15.x, python 3.14.4
versus baseline_lzma at full 10⁹: S=211,776,421 → Δ = −1,896,296 (−0.90%)
verdict: PREPROCESSOR_WINS
```

## Verdict vocabulary

The agent prompts use a fixed set of verdicts so result PRs are scannable. Use these by name:

**`empirical_reality` (the bench engineer):**
- `PREPROCESSOR_WINS` — `S` strictly less than the comparison baseline at the same scope
- `PREPROCESSOR_LOSES` — `S` strictly greater
- `BACKEND_DEPENDENT` — wins under one back-end, loses under another (note the matrix)
- `INCOMPLETE` — required measurements missing (no full-corpus run, no determinism check, no `roundtrip_ok`)
- `REPRODUCED` / `NOT_REPRODUCED` — for audits of someone else's claimed result
- `DETERMINISTIC` / `NON_DETERMINISTIC` — for cross-host SHA256 comparison

**`skeptic_referee` (the reviewer):**
- `PASS` — every audit step succeeded
- `FAIL` — list every failed step and the principle violated
- `NEEDS-INFO` — list missing artifacts and the exact command that produces them

Avoid `looks_promising`, `interesting`, `creative`. Those are reactions, not verdicts. They get retired by `empirical_reality`.

## Kill conditions

Phase plans (in `agents/` and tracked-progress docs) gate proceeding to the next phase on **measured** kill conditions, not adjectives. The format:

```
Phase X — <what>
- Pass:  <named metric> < <numeric threshold> at <scope> with <determinism contract>
- Kill:  <named metric> ≥ <numeric threshold> at <scope> → retire and document why
```

Concrete example (Phase A AST baseline):

```
- Pass:  S_AST(10 MB) ≤ S_lzma(10 MB) AND patch_fraction ≤ 10% AND roundtrip_ok = true
- Kill:  any of the above fails → AST primary representation retired for this corpus
```

A program that fails its phase kill condition is not a failure of the project; it's an empirical answer to a hypothesis. Document the result in `results/<id>/`, leave the program in place, and proceed.

## Compression math (formal)

This section is the formal reference for budgeting any grammar-class, AST-class, or preprocessor-class program against the contest score. Conclusions are stated with derivations; the load-bearing constants are anchored on substrate-specific measurements, not generic estimates. Use this when deciding whether a feature is worth building, not just when reporting results.

### SLP / grammar bit-encoding cost

A Straight-Line Program (SLP) is an acyclic context-free grammar with strict ordering: each non-terminal `X_i` may reference only `X_j` and `X_k` with `j, k < i`. This rules out infinite expansion (the failure mode is RAM exhaustion from exponentially-deep trees, not non-termination — zip bombs are a separate phenomenon: nested-archive expansion, not SLP recursion).

For a doubling grammar `X_n → X_{n−1} X_{n−1}`, expanded length is `2^(n−1)` symbols. The bit-encoding cost is **not** linear in `n`:

```
|encode(G)| = Σ_{i=2}^{n} 2 · ⌈log₂(i + |Σ|)⌉  =  O(n log n) bits
```

The compressed-side bit cost grows superlinearly because each rule body of length 2 contains two pointers, each costing `O(log n)` bits. The compression ratio is exponential `(2^n / (n log n))`, but the compressed side is `n log n`, not `n`. This determines the break-even depth for grammar compression: doubling-style grammars need depth `~log N` to beat literal encoding of an `N`-symbol output.

### Pointer cost: Shannon bound vs. uniform bound

The cost of encoding one rule reference under arithmetic coding is

```
Cost(X_i) = ⌈ -log₂ p(X_i) ⌉ bits
```

where `p(X_i)` is the empirical (or modeled) probability of `X_i` in the rule-reference stream. This is the **Shannon bound** — the minimum achievable by any uniquely decodable code.

The frequently-cited `⌈log₂(|V| + |Σ|)⌉` is the **uniform-distribution upper bound**, achieved when all symbols are equiprobable. Real grammar compressors (RePair with arithmetic coding, Sequitur, gzpv) achieve close to the Shannon bound — often 30–50% better than uniform on natural-text grammars where rule frequencies are heavy-tailed.

**Use the Shannon bound for budgeting.** Citing the uniform bound as the cost of a pointer overstates pointer cost and pushes admission thresholds artificially upward.

### Rule admission threshold

The threshold depends on **how rules are encoded**. Two regimes:

**(A) Inline-encoded rules** — definition appears in the byte stream as `marker + body_symbols`. Each definition costs `~2c` where `c = ⌈log₂(|V|+|Σ|)⌉`. Each occurrence of the digram `AB` costs `c` after admission (one symbol) or `2c` before (two symbols).

```
Admit iff:  f_AB · 2c  >  f_AB · c + 2c
            ⟺  f_AB · c > 2c
            ⟺  f_AB > 2
            ⟺  f_AB ≥ 3
```

**(B) Separate-table-encoded rules (RePair, Sequitur)** — definitions live in a separate rule-table region. Defining a rule consumes one new symbol in the alphabet but does not write the body inline; the body is referenced through the table.

```
Admit iff:  f_AB · 2c  >  f_AB · c + c
            ⟺  f_AB · c > c
            ⟺  f_AB > 1
            ⟺  f_AB ≥ 2
```

**RePair (Larsson & Moffat 1999) and Sequitur (Nevill-Manning & Witten 1997) both use scheme (B)** and admit at `f ≥ 2`. A tree miner that hardcodes `f ≥ 3` as the floor leaves digrams with exactly 2 occurrences un-admitted — small but real compression on the table.

The admission floor in this repo: **`f ≥ 2` for separate-table encodings; `f ≥ 3` for inline encodings**. Document which regime your encoder uses; the math depends on it.

### Total archive cost

For a structural-grammar approach with grammar `G`, patch stream `P`, and parser source counted in `program_size`:

```
S = compressed_size + program_size

compressed_size = |encode(G)| + L_patch
                = |encode(G)| + Σ_{i ∈ P} ⌈ -log₂ p̂(x_i | x_{<i}) ⌉

program_size   = |parser_source| + |miner_source| + (other inlined files)
```

`|encode(G)|` is the bit-length of the grammar under the chosen rule-encoding. **Do not use `K(G)` (Kolmogorov complexity)** in budget arithmetic — it is uncomputable and does not equal `|encode(G)|` for any practical encoder. `K(G)` is a theoretical lower bound; budget against the actually-achievable encoding.

`p̂(x_i | x_{<i})` is **the substrate's coder's modeled probability** on the patch stream, not a generic byte-coder estimate. Patch-entropy substitution is the most common error in pre-build estimation:

| substrate | typical patch b/B | source |
|---|---:|---|
| byte-level n-gram (PPM-tiny) | 4–6 | order-N model on raw bytes |
| LZMA | 2.5–4 | match finder + range coder |
| cmix | 1.0–1.5 | full mixer + dictionary; patches still natural-text-like |
| theoretical worst case | 8 | uniform-random bytes; **does not apply to natural patches** |

Empirically on `enwik9`, patches under cmix are dominated by inline HTML, malformed wikitext, and entity escapes — all natural-language-shaped. Citing 8 b/B (or even 3 b/B under cmix) is adversarial paranoia, not measurement.

### The joint (Δstruct, f) break-even

A grammar/AST representation is net-positive on a given substrate iff the structural improvement on the structured fraction outweighs the patch cost on the residual fraction, after subtracting the parser/miner overhead amortized across the corpus. The honest formula:

```
            Δ_struct − (|parser| + |miner|) · 8/n
f  <  ───────────────────────────────────────────
              b_patch^{post-split}  −  b_struct
```

where:

- `n` is input size in bytes (10⁹ for full `enwik9`)
- `Δ_struct = b_baseline − b_struct` (improvement on the structured fraction; **measured**, never extrapolated)
- `b_patch^{post-split}` is the substrate's coder b/B on the **isolated patch stream** — typically 10–30% worse than the same coder on the same bytes inline, because separation strips context. Use the post-split number.
- The parser/miner term in the numerator is the program-size cost normalized to b/B (`|parser|` in bytes, multiplied by 8 to get bits, divided by `n` to get b/B).

**The kill condition cannot be stated as a fixed `f ≤ X%` threshold.** It must be a joint condition on `(Δ_struct, f, b_patch, parser_size)` — and `Δ_struct` is unmeasured before the prototype runs, so the threshold itself is unmeasured before then.

### Worked examples

**Example 1: lzma substrate, light parser, hypothetical structural delta.**

```
b_baseline = 1.694          # baseline_lzma full-corpus b/B
b_struct   = 1.5            # hypothetical: AST helps lzma by 0.2 b/B
Δ_struct   = 0.194
b_patch    = 2.5            # lzma on isolated patches
parser     = 5,000 bytes    # ~150 LOC Python
n          = 10⁹

f < (0.194 - 4 × 10⁻⁵) / (2.5 - 1.5)  ≈  19%
```

So under lzma with this Δ_struct, an AST representation is viable up to 19% patch fraction. The 8% rule-of-thumb from the prior rewrite was **anchored on the wrong patch entropy** (3 instead of 2.5 wouldn't matter much; the bigger error was treating patches as 8 b/B-class).

**Example 2: cmix substrate, modest structural delta.**

```
b_baseline = 0.886          # cmix full-corpus b/B (fx2-cmix-class)
b_struct   = 0.85           # AST helps cmix by 0.036 b/B
Δ_struct   = 0.036
b_patch    = 1.2            # cmix on isolated patches
parser     = 5,000 bytes
n          = 10⁹

f < (0.036 - 4 × 10⁻⁵) / (1.2 - 0.85)  ≈  10%
```

Tighter: ~10% on cmix because Δ_struct is much smaller. cmix already extracts most of the redundancy that an AST representation would expose.

**Example 3: cmix substrate, heavier parser, ambitious Δ_struct.**

```
b_baseline = 0.886
b_struct   = 0.80           # AST helps by 0.086 b/B (optimistic)
Δ_struct   = 0.086
b_patch    = 1.2
parser     = 200,000 bytes  # full wikitext parser, embedded
n          = 10⁹

f < (0.086 - 1.6 × 10⁻³) / (1.2 - 0.8)  ≈  21%
```

The parser cost is non-trivial at 200 KB but doesn't dominate at 10⁹ bytes. At 10⁸ bytes (a 100 MB diagnostic prefix), the parser term is `8 × 200,000 / 10⁸ = 1.6 × 10⁻²` b/B, and the threshold drops to ~17%. At 10⁷ bytes it drops to ~0%, i.e. the parser can't pay for itself at that scale. **Parser amortization is scope-dependent**; small-slice diagnostics under-favor heavy parsers.

### Hard rules

These rules govern any grammar- or AST-class proposal in this repo:

1. **`|encode(G)|`, never `K(G)`.** Kolmogorov complexity is uncomputable; it cannot anchor a budget formula.
2. **Patch entropy is what the substrate's coder achieves on the isolated patch stream.** Not a generic estimate. Not the inline measurement. Measure it after splitting.
3. **Rule admission floor: `f ≥ 2` for separate-table encoders, `f ≥ 3` for inline encoders.** State which one your encoder uses.
4. **Pointer cost is the Shannon bound `−log₂ p(X_i)`, not the uniform `log₂(|V|+|Σ|)`.** Use arithmetic coding or your floor is overstated.
5. **Parser and miner source ship in `program_size`.** Their bytes count 1:1 against `S`. Amortize over `n`; check the threshold at the *measured* scope.
6. **Phase A's kill condition is a joint `(Δ_struct, f)` bound, not a fixed `f ≤ 10%`.** State the formula above with the substrate-specific constants and report whether the measured `(Δ_struct, f)` lands in the net-positive region.

If a proposed program cannot state where in the (Δ_struct, f) plane it expects to land — under measured `b_patch^{post-split}` and accounting for parser size — the proposal is incomplete regardless of how clever the structural mining looks.

## Cross-host determinism protocol

Single-host determinism (`--check-determinism` flag) verifies that two consecutive `compress()` calls on this machine produce byte-identical output. This catches obvious non-determinism (random seeds, hash randomization, time-dependent state) but does *not* catch float-arithmetic drift between machines.

Cross-host determinism requires **two distinct hosts** producing byte-identical archives:

```bash
# host A
python3 lib/driver.py <id> --check-determinism --data data/fixture_10mb.bin
cp results/<id>/<timestamp>.json /tmp/host_a_results/

# host B (the hourly cloud routine is wired up as host B)
python3 lib/driver.py <id> --check-determinism --data data/fixture_10mb.bin
# routine commits results/<id>/<timestamp>.json into a PR

# compare
python3 lib/compare_determinism.py --host-a /tmp/host_a_results/ --host-b results-from-pr/
```

The comparator emits exactly one of `DETERMINISTIC` / `NON_DETERMINISTIC` / `INCOMPARABLE` / `ONLY_HOST_A` / `ONLY_HOST_B` per program. **No program is contest-eligible until it produces `DETERMINISTIC` on at least one fixture across two distinct hosts.** Single-host determinism is necessary but not sufficient.

The deterministic fixture (`lib/fixture.py`) generates a 10 MB synthetic enwik-like input from a fixed seed; both hosts produce identical bytes from the same seed. This avoids requiring both hosts to download the full 1 GB `enwik9.zip`.

## Usage

```bash
# fetch + extract dataset (one time)
python3 bench.py --setup

# run one program
python3 lib/driver.py baseline_lzma

# run all programs in index.json and refresh the leaderboard
python3 bench.py

# add a new program: copy a baseline, edit, register in index.json
cp -r programs/baseline_lzma programs/my_attempt
$EDITOR programs/my_attempt/program.py
python3 bench.py --register my_attempt
```

## Adding programs

Drop a directory under `programs/`, then either:
- run `python3 bench.py --register <id>` to append to `index.json`, or
- edit `index.json` directly under `"programs"`.

Programs that aren't in `index.json` are ignored by `bench.py`.

## Agents

System prompts in `agents/` define personas for working on this challenge:

| id                 | realm                          | role |
| ------------------ | ------------------------------ | ---- |
| `hutter_contender` | legitimate compression         | serious entrant chasing the prize threshold |
| `skeptic_referee`  | validation                     | adversarial reviewer; rejects bullshit |
| `lm_explorer`      | language-model-as-coder        | explore neural-LM-driven arithmetic coding |
| `empirical_reality`| measurement-discipline         | forces byte accounting and measured backend deltas |
| `dac_crackpot`     | parody / red-team fixture      | crackpot persona used as test material for the skeptic — **do not implement** |

Index of agents is in `index.json` under `"agents"`. The DAC fixture is intentional: it is the adversary the skeptic is calibrated to demolish.

## Public algorithms — what's at the top, what each does, where the leverage is

Knowing the leaderboard names is not enough; understanding the *mechanisms* of the top entrants is what tells a contributor which attack surface is unmined. This section is a triage map. Sources: each entrant's public README, Mahoney's *Data Compression Explained*, Knoll's cmix repo, Skibiński's WRT/XWRT papers.

### The model-class lineage on `enwik9`

Compression on natural-language corpora has gone through five distinct model classes, each marking a step-change. Best `enwik9` archive size for each class (approximate; full-corpus, decompressor-included where applicable):

| class | exemplar | mechanism in one sentence | b/B floor on enwik9 | S floor (10⁹) |
|---|---|---|---:|---:|
| LZ77 + Huffman | gzip / DEFLATE | sliding-window match references + Huffman-coded literals | ~2.58 | ~322 MB |
| BWT + RLE + Huffman | bzip2 | block-sort the input, run-length the BWT output, Huffman | ~2.03 | ~254 MB |
| LZ77 + range coder | xz / LZMA2 | bigger sliding window + arithmetic-coded match flags | ~1.58 | ~198 MB |
| PPM (variable-order context tries) | PPMd, PPMonstr | predict next byte from order-N suffix tree of prior bytes | ~1.30 | ~165 MB |
| Context mixing (CM) + arithmetic coder | PAQ8 family | hundreds of small models combined by an online-trained mixer | ~1.00 | ~125 MB |
| CM + neural mixer + dictionary | cmix lineage | CM + LSTM/online mixer + 12 MB English dictionary + SSE | ~0.886 | ~111 MB |

Each step-change represents a *different model class*, not a parameter sweep. Going from gzip's ~322 MB to xz's ~198 MB was not "tune gzip harder"; it was switch the entropy coder family. Going from xz's ~198 MB to cmix's ~111 MB was not "tune xz harder"; it was switch from match-based modeling to context-mixing. **Every plateau in this table is a model-class ceiling, not an engineering plateau.** The Hutter Prize leaderboard sits inside the bottom row.

### Top public Hutter Prize entrants

| year | entrant | total `S` on enwik9 | over phda9 | model class |
|---:|---|---:|---:|---|
| 2024 | **fx2-cmix** (Kaido Orav & Byron Knoll) | **110,793,128** | −5.04% | CM + neural mixer + WRT + Single-Pass Wikipedia Transform |
| 2024 | fx-cmix (Kaido Orav) | 112,578,322 | −3.51% | CM + neural mixer + heavy preprocessing |
| 2023 | fast cmix (Saurabh Kumar) | 114,156,155 | −2.16% | CM + tighter cmix-derived pipeline |
| 2021 | starlit (Artemiy Margaritov) | 115,352,938 | −1.13% | cmix + Doc2Vec article reordering |
| 2017 (pre-prize) | phda9 v1.8 (Alexander Rhatushnyak) | 116,673,681 | (baseline) | hand-tuned context model |

`fx2-cmix` is the bar to beat. The 5.04 MB delta from `phda9` to `fx2-cmix` represents multiple public leaderboard generations across multiple authors, each shaving sub-percent. Improvements at this end of the curve are millimetric.

### Per-entrant: what each adds

**phda9 (Rhatushnyak, 2017)** — Hand-tuned context model with a custom dictionary, descended from the PAQ family. The base predictor is a context tree with carefully chosen orders and indirect contexts. No public neural component. The "phda" series predates cmix's neural-mixer architecture; the architectural reason it is no longer SOTA is that hand-tuned mixer weights cannot match online-trained mixer weights on this corpus. *Attack surface*: the only one in the leaderboard without a learned mixer.

**cmix (Byron Knoll, base — not in the leaderboard above; ~0.92 b/B in baseline form)** — The substrate that all newer entries build on. Components:
- *Preprocessor* — WRT-style word replacement using a ~12 MB English dictionary embedded in the binary; converts frequent words to 1–3 byte codes, preserving reversibility.
- *Context bank* — ~2,000 context families: order-N byte n-grams (N up to ~10), word n-grams, sparse contexts, indirect contexts, match models, special-purpose models for numbers / dates / XML tags.
- *Mixer* — small online-adapted neural mixer (logistic regression with backpropagation, plus an LSTM in newer versions). Adapted online during compression; decoder reproduces by replaying.
- *SSE* (Secondary Symbol Estimation) — calibration table that re-maps mixer output to empirically-observed probabilities.
- *Arithmetic coder* — encodes each bit at the calibrated probability.

cmix is the **operational reference** for everything in this repo. Attack surface: the static 12 MB English dictionary is the largest single byte cost in the decompressor; reducing or replacing it is one direction. The mixer architecture is another (cmix uses a small ensemble; bigger doesn't pay).

**starlit (Margaritov, 2021)** — cmix + a preprocessing pass that **reorders articles** by Doc2Vec similarity before passing to cmix. The intuition: similar articles compress better when adjacent (more long-range matches, more context overlap). The reordering map ships in the decompressor. Gain: ~1.13% over phda9. *Attack surface*: confirms cross-article structural similarity is exploitable. The Doc2Vec model is too large to ship inline; the ordering map is what's stored.

**fast cmix (Kumar, 2023)** — Tighter pipeline derived from cmix, with reduced runtime to fit the official compute envelope on lighter hardware. Architecture is cmix + minor tweaks; gain is mostly engineering, not new ideas. *Attack surface*: shows that the contest's compute envelope is binding.

**fx-cmix / fx2-cmix (Orav, 2024)** — Current record. Builds on cmix with:
- **Single-Pass Wikipedia Transform** — a custom preprocessor that recognizes wikitext templates and links structurally (`[|` markers), routing them through a separate stream from prose. This is the most architecturally significant addition since cmix.
- **Multi-stream construction** — four parallel word-stream channels with stemmer-based routing.
- **Pruned mixers** — drop low-information context families; gain from fewer, higher-quality predictors.

Gain over fast-cmix: ~3% (~3.4 MB). Cumulative gain over phda9: 5.04 MB (5.04% in archive bytes). *Attack surface*: the Single-Pass Wikipedia Transform is structural — it suggests a path forward through still-deeper structural awareness (template-position contexts, entity catalogs, see this repo's `cmix_sidecar_v1` plan).

### Where the unmined leverage is (per the active research synthesis in this repo)

The 5.04 MB phda9→fx2-cmix delta is dominated by structural Wikipedia-aware preprocessing. cmix-substrate gains *not yet exploited* on this corpus, in approximate order of predicted leverage:

| feature | mechanism | predicted gain | published in any entry? |
|---|---|---:|---|
| Subtree-class fingerprints | hash closed-template shape into a small int; recency-MTF; into mixer | 2–4% | No |
| Online entity catalog | `[[X]]` builds an integer-keyed table; "you are inside entity #N" as context | 2–4% | No (closest: cmix's word codes) |
| Long-range structural dedup | online suffix-array / FM-index extending the match window beyond cmix's sliding window | 2–4% | No |
| Integer-quantized SSM as context | small online-trained Mamba-class recurrence; one extra mixer input | 2–5% | No (Bellard's NNCP is a standalone neural coder, not a cmix context) |
| Template-position context | `(template_id, arg_index)` from a wikitext state machine | 3–6% | Partially (fx2-cmix's wiki transform; not as a typed context family) |
| Article-class rolling hash | hash `(title-prefix, first-infobox-class, category-tail)` per page | 1–2% | No |

These are the targets in this repo's `cmix_sidecar_v1` plan. The conservative composition (with overlap discounts) is 6–11% below cmix → S in [99, 105] MB. That clears the prize threshold and approaches the 10% target.

### What is *not* a path forward

The reject list in this repo's discipline (no static dictionaries, no float parser state, no lossy transforms, mandatory cross-host SHA256, every byte counted) rules out:

- Multi-billion-parameter pretrained LLMs as the predictor — weights count 1:1 in `program_size`; a 10 GB model needs to save 10 GB of archive vs. cmix to break even, which it cannot.
- Static word/title/entity dictionaries that ship in the decompressor — the budget for these is dominated by cmix's existing 12 MB; adding more is rarely net-positive.
- Lossy normalizations (date format canonicalization, whitespace collapse, etc.) — break roundtrip.
- "Recursive self-referential compression" claims that don't track where the bits go (DAC, fractal text compression, etc.) — rejected by the counting argument before any code is written; calibration fixture in `agents/dac_crackpot.md`.

### External leaderboard data

`index.json.external_leaderboard` carries the same data in machine-readable form (date, author, decompressor name, `total_size`). Updates land when a new record is announced at http://prize.hutter1.net/. The figure of merit is `total_size`, lower-is-better. Prize threshold for the next payout: `109,685,197`.
