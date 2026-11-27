# Preregistration: `A1AD` Construction-DAG Headers & Native Deployment Encoder Controls

**Status:** Preregistered from A1a CPU development evidence ([`DEV_REPORT.md`](DEV_REPORT.md), [`dev_summary.json`](dev_summary.json)). No sealed test corpus or fresh holdout has been opened. The tested multi-node bundle arm (`A1AB` / `B_A`/`B_B`/`B_C`) is **closed** (`FAIL` on CodeNet `primary`) and is explicitly excluded from holdout advancement.

## 1. Scope & Motivation

A1a development isolated two verifiable, non-bundle mechanisms worth testing on fresh held-out corpora:

1. **`A1AD` Construction-DAG Headers (25.0%–51.1% header reduction in dev):**
   Replacing flat literal dictionaries (`A1AF`, `1 + |e|` per entry) with the self-contained construction-DAG header (`A1AD`, dynamic bit-width pair edges `2 * ceil(log2(i))` for closed vocabularies, hybrid pair/literal/list tags for open vocabularies) keeps the emitted vocabulary, canonical Huffman code table, and coded payload **identical** while reducing header bytes by 25.0%–30.6% for open vocabularies and 35.9%–51.1% for closed vocabularies.
2. **Native Deployment Encoder Controls:**
   Development validation proved that constituent closure alone does not guarantee reachability under greedy rank-ordered encoders: live `tiktoken==0.14.0` confirmed `236 / 3,861` UTF-8 tokens (`237 / 3,924` full-table; `274 / 3,924` prefix-monotone) in `closed-K4096` are shadowed and unreachable under `byte_pair_merge`, whereas `bpe-K4096` has `0` shadowed tokens (`3,843 / 3,843` live UTF-8; `3,924 / 3,924` full-table).

## 2. Frozen Specification, Code, and Dependency Hashes

Every verification run on fresh corpora MUST verify exact SHA-256 identity of the frozen serializer, standalone decoder, specification, encoder validator, and pinned `tiktoken` dependency manifest before touching any fresh corpus:

| Artifact | Frozen SHA-256 | Role |
| --- | --- | --- |
| `FORMAT.md` | `1be36803ea554b16f46a1db95225b56ec832c5e843ef9cf2519b2eafde3203f3` | Complete binary specification of `A1AF` and `A1AD` |
| `headers.py` | `5a14f0d5d2e46b20060c8b4b2541c804a0f0b95b465789730c30f7e45a4e6a53` | Dual `A1AF`/`A1AD` serializer and train-only Huffman table fitter |
| `independent_decode.py` | `03ec092b5dad49cc33531af5dea72ef2fcc80f402860b947904256ad57fbe114` | Standalone stdlib-only decoder (zero shared code with `headers.py`) |
| `validate_encoders.py` | `a689744e473a15818b7342a280b7233b2c5dddfd56d69991e9fab24e97ccd5f9` | Live HF `tokenizers` + live `tiktoken` + pure-Python `byte_ranks` validator |
| `requirements-tiktoken.txt` | `5ef7c35fecdb702f6b599aa7b096e6e891143258aadd7bf1df0389c6d40d0020` | Exact pinned `tiktoken==0.14.0` environment manifest |

Vocabularies and canonical Huffman code tables remain frozen from CodeNet `primary` training only (`closure-holdout-v1` / `a1a-fixed-budget-v1/out/chains/`); NO parameter, code length, or merge rank may be fitted on any fresh corpus.

## 3. Preregistered Arms

Evaluated on fresh held-out corpora (disjoint from CodeNet `primary`, `dev`, `fresh`, `fresh2`, `Express`, `ramda`, and `TheAlgorithms/Python`):

- **Vocabulary arms (frozen from CodeNet `primary`):**
  1. `open` (`exact-entry-s1-whole`), serialized under `A1AF` and `A1AD` (hybrid mode)
  2. `open-byte` (`open-byte-ext`), serialized under `A1AF` and `A1AD` (hybrid mode)
  3. `exact-closed` (`exact-closed-s1-whole` / `pair-ext`), serialized under `A1AF` and `A1AD` (pure-pair mode)
  4. `pair-byte` (`pair-byte-exact-full`), serialized under `A1AF` and `A1AD` (pure-pair mode)
  5. `bpe` (`bpe-ext` with exact `M` merges), serialized under `A1AF` and `A1AD` (pure-pair mode)
- **Codec & deployment encoder controls:**
  - `zstd -19` lean-framed (`--no-dictID --no-check`, content size present) with primary-trained 8 KiB dict, 32 KiB dict, and no-dict, measuring sequential complete bytes, random-access complete bytes, and in-process C `libzstd` per-record decode latency (p50/p95/p99).
  - Native encoders scored separately alongside common minimum-token DP:
    - Hugging Face `tokenizers` BPE (`ByteLevel` bijective byte alphabet and stock GPT-2 `ByteLevel` pre-tokenizer)
    - `sentencepiece` Unigram (`byte_fallback=True`, native Viterbi vs common DP)
    - Live pinned `tiktoken==0.14.0` `tiktoken.Encoding` (`byte_pair_merge` reachability/shadowing audit + byte-exact UTF-8 round-trip + exact token-stream parity with pure-Python `byte_ranks`)
    - Greedy left-to-right longest-match (AC/trie)

## 4. Operating Budgets & Complete-Bits Comparator

All vocabulary arms are evaluated at TWO frozen primary-determined header budgets (matching `open@84` and `open@3924`) plus matched emitted slots:
- **Common `A1AD` header budgets:** `<= 878 B` (small) and `<= 33,241 B` (large).
- **Matched emitted slots (secondary comparator):** `84` and `3,924` fragments.
- **Primary archive comparator:** `complete_bits = 8 * len(archive)` (sequential self-contained archive counting every header, DAG, table, framing, and payload byte) AND `random_access_complete_bits` (per-file byte padding + per-file length varint).
- **Break-even horizon $M^*$:** Reported in both bytes and equivalent file counts on every fresh corpus for `A1AD` vs `A1AF`, `exact-closed` vs `open`/`open-byte`, and `A1AD` vs lean-framed `zstd-19`.

## 5. Pass / Fail Gates for Fresh-Corpus Verification

1. **Exact Round-Trip & Structural Integrity Gate (hard gate):**
   - `independent_decode.py` recovers **100% of files byte-for-byte** across every `A1AF` and `A1AD` archive (`0` mismatches, `< 8` zero padding bits, exact Kraft sum `== 1`).
   - All 6 negative corruption controls (`dag_self_edge`, `dag_edge_swap`, `rank_inversion`, `rank_duplicate`, `huffman_length_corrupt`, `flat_payload_bitflip`) fail replay with `FormatError`.
2. **`A1AD` Header & Complete-Bits Gate:**
   - For every fixed vocabulary and corpus, `A1AD` matches `A1AF` payload bytes identically (`0` payload difference) and strictly reduces `complete_bits` (`A1AD < A1AF`).
   - At the large `A1AD` budget (`<= 33,241 B`), test whether `exact-closed` (`A1AD`) achieves strictly lower `complete_bits` and fewer min-DP tokens than `open` (`A1AD`) across fresh corpora, with two-sided paired per-unit sign test (`p < 0.05`).
   - Report honest distance to lean-framed `zstd-19` (8 KiB dict) in `complete_bits`, p95 per-record decode latency, and break-even horizon $M^*$ without claiming codec dominance unless `complete_bits` is actually lower at the tested corpus size.
3. **Deployment Encoder Controls Gate:**
   - Live `tokenizers` and live pinned `tiktoken==0.14.0` pass 100% byte-exact round-trip on all valid UTF-8 fresh files and 100% token-stream parity with reference replay (`0` mismatches).
   - Live `tiktoken` reachability/shadowing counts match `validate_encoders.py`'s full-table `byte_ranks` validator identically (`0` discrepancies), reporting realized native-encoder token inflation vs common minimum-token DP for every encoder control.
