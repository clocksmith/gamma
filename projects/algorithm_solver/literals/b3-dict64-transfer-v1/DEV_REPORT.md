# B3 Development Report: One Transferable 64-Entry Dictionary

## Decisions (Reported Separately & Enforced Programmatically)

- **matched80 Witness Decision:** `PASS` (80/80 zero-escape, 8,412/8,412 tests, max `1.0331x` steps)
- **Dev Transfer Decision (Pass 1, initial rewriter):** `FAIL` (`72/83` = `86.75%` < `90.0%` minimum bar; previous `PASS` label corrected to `FAIL`)
- **Dev Transfer Decision (Pass 2, single general transform, `B3H1` Huffman):** `PASS` (`76/83` = `91.57%`, `wrong_acceptances=0`, complete bits `176944` vs `219656`)
- **Dev Transfer Decision (Pass 2, `B3P1` Fixed-6-bit):** `PASS` (`76/83` = `91.57%`, complete bits `198848` vs `277152` fixed-8 and `219656` Huffman)
- **dev_gate Verification:** `PASS` (10/10 gates & negative controls passed)
- **Frozen Dictionary SHA-256 (`artifacts/frozen_dict64.json`):** `70166bd0f6b84af31ab9bc5479cab5bae50b6fe3bb000fdeca85b8e0bb87c135` (byte-for-byte unchanged across Pass 1 and Pass 2; step ceiling fixed at `1.1x`)
- **Next-Stage Gate Note:** PASS on spent dev transfer earns sealed transfer evaluation only; B4 still requires sealed transfer success AND explicit compute approval.

> Contract: `dev_transfer` is `PASS` ONLY if `(accepted / total >= 0.90)` AND `(wrong_acceptances == 0)` AND `(complete_bits <= baseline_complete_bits)`; otherwise `FAIL`. Witness (`matched80`) and dev transfer (83 disjoint spent JS problems) are strictly separated decisions. No sealed clusters were opened, no packages were installed, and no GPU/network compute was used.

## 1. Cohorts & Baseline Rank Pins

- **matched80:** 80 JS programs, 8412 frozen behavior tests, verified byte-for-byte against Git pin `59ff04415ff2afd04ff2ed451340f4f02852bf18` with 80/80 trailing newlines preserved.
  - Raw `canonical` baseline (40467 B): alphabet=92, exact unrestricted rank min=79, exact witnessed rank min=92.
  - Raw `compact` baseline (18542 B): alphabet=92, exact unrestricted rank min=79, exact witnessed rank min=92.
  - Raw `original` baseline (57236 B): alphabet=93.
- **Separate Spent Dev Transfer Cohort:** 83 disjoint JS problems (4878 frozen cases, 50689 raw bytes) from `continuation-a-20261028-v1, continuation-d-20261028-v1, continuation-f-20261028-v1, continuation-h-20261028-v1, continuation-j-20261028-v1, continuation-l-20261028-v1, continuation-n-20261028-v1, continuation-o-20261028-v1`, programmatically verified 0 overlap with `matched80` and 0 overlap with reserved/protected IDs.

## 2. Separate Coding Regimes: `B3H1` (Huffman) vs `B3P1` (Fixed-6-Bit)

### 2a. `matched80` Witness (80 Programs, 0 Escapes, 64 Entries)

| Package / Comparator | Coding Regime | Package Bits (excl. dec) | Decoder Bits | Complete Bits | Delta vs Canonical Huff BPE-256 | Delta vs Canonical Fixed-8 BPE-256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **Arm 3 `B3H1` (Huffman)** | Canonical Huffman over 64-entry stream | **71640** | **9840** | **81480** | **-1304** | **-9048** |
| **Arm 3 `B3P1` (Fixed-6-bit)** | Fixed 6 bits/token (no Huffman) | **83208** | **9840** | **93048** | **+10264** | **+2520** |
| Arm 4 BPE-256 `canonical` (Huffman) | Raw `canonical` 256-entry BPE + Huff | 82784 | 0 (free) | 82784 | +0 | -7744 |
| Arm 4 BPE-256 `canonical` (Fixed-8) | Raw `canonical` 256-entry BPE + F8 | 90528 | 0 (free) | 90528 | +7744 | +0 |
| Arm 4 BPE-256 `original` (Huffman) | Raw `original` 256-entry BPE + Huff | 165872 | 0 (free) | 165872 | +83088 | +75344 |
| Arm 4 BPE-256 `original` (Fixed-8) | Raw `original` 256-entry BPE + F8 | 180504 | 0 (free) | 180504 | +97720 | +89976 |
| Arm 4 BPE-256 `compact`* (Huffman / F8) | Pre-minified `compact` ceiling | 59560 / 64392 | 0 (free) | 59560 / 64392 | -23224 | -26136 |

### 2b. Disjoint Spent Dev Transfer (83 Problems, Pass 2, Frozen Dict64 + Charged Fallback)

| Package / Comparator | Coding Regime | Package Bits (excl. dec) | Decoder Bits | Complete Bits | Delta vs Frozen `m80` BPE-255 Huff | Delta vs Frozen `m80` BPE-255 Fixed-8 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **B3 Transfer `B3H1` (Huffman)** | Frozen Huff 64-entry + charged fallback (`frozen_matched80_bpe255_escape`) | **161336** | **15608** | **176944** | **-42712** | **-100208** |
| **B3 Transfer `B3P1` (Fixed-6-bit)** | Fixed 6 bits/token + charged fallback (`frozen_matched80_bpe255_escape`) | **183240** | **15608** | **198848** | **-20808** | **-78304** |
| Frozen `matched80` BPE-255+esc (`canonical` Huff) | Frozen raw BPE + Huffman | 219656 | 0 (free) | 219656 | +0 | -57496 |
| Frozen `matched80` BPE-255+esc (`canonical` F8) | Frozen raw BPE + Fixed-8 | 277152 | 0 (free) | 277152 | +57496 | +0 |
| Frozen `matched80` BPE-255+esc (`original` Huff / F8) | Frozen raw BPE (`original`) | 221056 / 266720 | 0 (free) | 221056 / 266720 | +1400 | -10432 |
| In-domain Dev BPE-256 (Oracle Huff / F8) | Fit directly on 83 transfer files | 175656 / 194824 | 0 (free) | 175656 / 194824 | -44000 | -82328 |

## 3. All 4 Required Arms on `matched80`

| Arm | Source / Policy | Alphabet / Slots | Coverage (0-esc) | Entries | Package Bits (excl. dec) | Decoder Bits | Complete Bits | Max Step Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Arm 1a (Raw flat @64) | Raw `canonical` (\n kept) | 92 chars / 0 learned | 64/80 (infeasible) | 64 | n/a | n/a | n/a | 1.0000x |
| Arm 1b (Raw flat @256) | Raw `canonical` (\n kept) | 92 chars / 164 learned | 80/80 | 256 | 72112 (Huff) / 74448 (F8) | 0 (ref) | 72112 | 1.0000x |
| Arm 2 (Fixed canonical @64) | Frozen rewriter + flat tiler | 37 singles / 27 multi | 80/80 (0 esc) | 64 | 73584 (B3H1) / 85584 (B3P1) | 9840 | 83424 (B3H1) / 95424 (B3P1) | <=1.1000x |
| **Arm 3 (Joint canonical @64)** | **Joint rewrite + witnessed dict64** | **37 singles / 27 multi** | **80/80 (0 esc)** | **64** | **71640 (B3H1) / 83208 (B3P1)** | **9840** | **81480 (B3H1) / 93048 (B3P1)** | **1.0331x** |
| Arm 4 (BPE-256 `canonical`) | Raw `canonical` BPE-256 (\n kept) | 92 base + 164 merges | 80/80 | 256 | 82784 (Huff) / 90528 (F8) | 0 (free) | 82784 (Huff) / 90528 (F8) | 1.0000x |
| Arm 4 (BPE-256 `original`) | Raw `original` BPE-256 (\n kept) | 93 base + 163 merges | 80/80 | 256 | 165872 (Huff) / 180504 (F8) | 0 (free) | 165872 (Huff) / 180504 (F8) | 1.0000x |
| Arm 4 (BPE-256 `compact`*) | Pre-minified `compact` BPE-256 | 92 base + 164 merges | 80/80 | 256 | 59560 (Huff) / 64392 (F8) | 0 (free) | 59560 (Huff) / 64392 (F8) | 1.0000x |

*Note on Arm 4 controls & decoders: `canonical` (40,467 B) and `original` (57,236 B) are unminified raw JS controls (`canonical` matches the exact 79 unrestricted / 92 witnessed minima of `witness-coverage-v1`); `compact` (18,542 B) is pre-minified by `scale-v2/generate.cjs` and logged separately. Both `B3H1` and `B3P1` witness packages charge `b3_witness_decoder.py` (1230 B = 9840 bits); charging the full transfer decoder (`b3_ref_decoder.py`, 15608 bits) yields 87248 bits (`B3H1`) and 98816 bits (`B3P1`).

## 4. Dev Transfer Pass 1 vs Pass 2 (Fixed Dict64 + Fixed 1.1x Step Ceiling)

- **Single General Pass-2 Rewriter Transformation:** General AST lowering of non-mutating numeric copy-sort (<expr>.slice().sort((a,b)=>a-b) and fresh [...].sort((a,b)=>a-b)) to a runtime-guarded Float64Array fast path (verifying Array.isArray, pristine .slice / [Symbol.iterator], dense copy c.every(Number.isFinite), and !c.some(Object.is.bind(null,-0)), falling back verbatim to the original JS comparator sort outside finite non-negative-zero numeric arrays) without changing frozen_dict64.json or the 1.1x step ceiling.
- **Frozen Dictionary Check:** `artifacts/frozen_dict64.json` SHA-256 = `70166bd0f6b84af31ab9bc5479cab5bae50b6fe3bb000fdeca85b8e0bb87c135` (identical before and after Pass 2; 0 dictionary entries changed).

| Pass | Rewriter `rewriter.mjs` SHA-256 | Accepted / Total | Coverage | Wrong Acceptances | Refusal Breakdown | `B3H1` Complete Bits | `B3P1` Fixed-6 Complete Bits | Decision (`>=90%` Bar) |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Pass 1 (initial) | `3dd7d6e114ee` | 72/83 | 86.75% | 0 | `{"step_ceiling_exceeded": 9, "unspellable_zero_escape": 2}` | 165496 | n/a (added in Pass 2) | **`FAIL`** |
| **Pass 2 (numeric copy-sort)** | `6bd15a99a6f8` | **76/83** (`+4`) | **91.57%** | **0** | `{"step_ceiling_exceeded": 5, "unspellable_zero_escape": 2}` | **176944** (`+11448`) | **198848** | **`PASS`** |

### Problem Family Transfer Breakdown (Pass 2, Every Uncovered Family Reported)

| Problem Family | Total | Accepted (0-esc) | Refused (Fallback) | Coverage |
| --- | ---: | ---: | ---: | ---: |
| `array_greedy_search_ds` | 6 | 6 | 0 | 100.0% |
| `general_algorithmic` | 15 | 13 | 2 | 86.7% |
| `geometry_matrix_graph` | 10 | 7 | 3 | 70.0% |
| `math_bitwise_combinatorics` | 19 | 19 | 0 | 100.0% |
| `string_window_sequence` | 33 | 31 | 2 | 93.9% |

- **Families with any refusal:** ['general_algorithmic', 'geometry_matrix_graph', 'string_window_sequence']
- **Completely uncovered families (0 accepted):** []
- **Single fixed canonical spellable:** 81/83.
- **Refusal reason counts:** `{"step_ceiling_exceeded": 5, "unspellable_zero_escape": 2}`
- **Top unspellable syntax/literal blockers:** `{" ": 1, "^": 1}`

## 5. Shared Spine Summary (`fidelity`, `complete_bits`, `measured_work`, `horizon` H*)

### Witness (`matched80`)
- **fidelity:** 80/80 covered (0 escapes), 8412/8412 frozen tests passed, 80/80 <= 1.1x steps (median=0.938093x, p95=1.001011x, max=1.033086x), independent decode=80/80, wrong_acceptances=0, changed_algorithms=0.
- **complete_bits (`B3H1` Huffman):** `81480` bits (`header=2720`, `stream=68920`, `decoder=9840`, `hidden_helpers=0`, explicit hoisted constants inside stream=`14259` bits across 50 programs).
- **complete_bits (`B3P1` Fixed-6-bit):** `93048` bits (`header=2200`, `stream=81008`, `decoder=9840`).
- **measured_work:** total wall=62.8098s (rewrite=0.2989s, arm2_build=6.3239s, arm3_selection=1.6601s, cand_verify=1.3495s, witness_reexec=0.2767s, decode=0.047393s, decode_p95=0.2198 ms/prog), peak RSS=143,441,920 B, measured steps=780,590 vs original 831,226 (agg ratio=0.939083x).
- **horizon H*:** `B3H1` vs Arm 4 `canonical` Huff BPE-256 = `73` programs (36926.1 raw B), vs `original` Huff = `11` programs; `B3P1` fixed-6 vs Arm 4 `canonical` Fixed-8 = `102` programs, vs `original` Fixed-8 = `10` programs.

### Dev Transfer (Disjoint 83 Spent JS Problems, Pass 2)
- **fidelity:** 76/83 accepted (0 escapes), 7 refused -> charged raw fallback, wrong_acceptances=0, accepted step ratio median=0.999984x / p95=1.041645x / max=1.093103x.
- **complete_bits (`B3H1` Huffman):** `176944` bits (`primary_header=2720`, `fallback_total=25496`, `covered_stream=133088`, `decoder=15608`; raw-UTF8 fallback option = `182264` bits).
- **complete_bits (`B3P1` Fixed-6-bit):** `198848` bits (`primary_header=2208`, `fallback_total=25496`, `covered_total=155528`, `decoder=15608`; raw-UTF8 fallback option = `204168` bits).
- **measured_work:** total wall=14.5512s (rewrite=0.7834s, selection=0.1679s, verify=2.6652s, decode=0.068401s, decode_p95=0.412 ms/prog, reexec=2.6332s), peak RSS=143,441,920 B, measured steps=32,159,865 vs original 31,950,456 on accepted programs.
- **horizon H*:** `B3H1` vs frozen `matched80` BPE-255 `canonical` Huff = `28` programs, vs in-domain dev BPE-256 Huff = `89` programs; `B3P1` fixed-6 vs frozen `matched80` BPE-255 `canonical` Fixed-8 = `18` programs, vs `canonical` Huff = `42` programs.

## 6. Diagnostics: Rewrite Yield, Dictionary Utilization & Runtime Tails

- **Rewrite yield (`matched80`):** 423/423 rewrite candidates verified & step-compliant; raw canonical 40,467 B -> Arm 3 rewritten 23,751 B (ratio 0.5869x vs canonical, 0.415x vs original).
- **Dictionary utilization:** `matched80` uses 64/64 entries (100.0%); min multi-char fit support = 3 programs (>=2 enforced). On dev transfer, 62/64 entries are used (96.9%); unused on transfer: `[' in ', 'throw(']`.
- **Changed algorithms:** `0` across both cohorts (strictly semantics-preserving AST canonicalization).
- **Witness top-5 runtime-step ratios:** #1046=1.0331x, #9=1.0075x, #14=1.0031x, #3=1.0011x, #58=1.0010x
- **Transfer top-5 accepted runtime-step ratios:** #3899=1.0931x, #3934=1.0660x, #3836=1.0646x, #3625=1.0416x, #3742=1.0381x

## 7. `dev_gate` Verification & Mandatory Negative Controls

| Gate / Negative Control | Status | Detail |
| --- | --- | --- |
| `G1_matched80_pin_and_rank_baselines` | **PASS** | pin=59ff04415ff2, compact=79/92, canonical=79/92, trailing_nl=80/80 |
| `G2_witness_independent_decode_zero_escapes` | **PASS** | 80/80 exact match across independent_decode, b3_witness_decoder, b3_ref_decoder, and B3P1; 0 escapes |
| `G3_dict64_witnessed_eligibility` | **PASS** | entries=64<=64, witnessed_ok=True, frozen_dict_sha256_ok=True (70166bd0f6b8), errors=[] |
| `G4_witness_tests_and_step_ceiling` | **PASS** | programs=80/80, cases=8412/8412, step<=1.1x=80/80, max_ratio=1.0331 |
| `G5_witness_complete_bits_le_arm4_bpe256` | **PASS** | B3H1_huff=81480 b (pkg=71640 + dec=9840) <= arm4_canonical_huff=82784 b & arm4_original_huff=165872 b; B3P1_fixed6=93048 b (pkg=83208 + dec=9840) [vs arm4_canonical_f8=90528 b, arm4_original_f8=180504 b, pre-minified compact_huff=59560 b] |
| `G6_dev_transfer_frozen_fallback_zero_wrong_acceptances` | **PASS** | accepted=76/83 (91.57%), fallback_ok=7, wrong_acceptances=0, b3h1_and_b3p1_decode_match=True, frozen_dict_sha256_ok=True, decision=PASS (label_contract_ok=True) |
| `NC1_hidden_helper_rejected` | **PASS** | {"name": "negative_control_1_hidden_helper", "passed": true, "subcheck_undeclared_free_helper_rejected": true, "subcheck_undeclared_reason": "undeclared_or_hidden_helper", "subcheck_injected_helper_rejected": true, "subcheck_injected_reason": "injected_hidden_helper_forbidden"} |
| `NC2_invalid_dict_id_rejected` | **PASS** | {"name": "negative_control_2_invalid_dict_id", "passed": true, "subcheck_b3p1_invalid_id_rejected": true, "subcheck_b3p1_error": "invalid dictionary ID 63 (vocab_len=5)", "subcheck_b3h1_over64_rejected_independent": true, "subcheck_b3h1_over64_rejected_ref_decoder": true, "subcheck_b3h1_error": "dictionary size 65 outside [1, 64]", "subcheck_b3h1_corrupt_huffman_rejected": true} |
| `NC3_step_ceiling_exceeded_rejected` | **PASS** | {"name": "negative_control_3_step_ceiling", "passed": true, "problem_id": 136, "all_outputs_correct": true, "original_steps": 3679, "slow_steps": 18232, "step_ratio": 4.9557, "rejected_by_1_1x_ceiling": true} |
| `NC4_numeric_sort_domain_guard` | **PASS** | {"name": "negative_control_4_numeric_sort_domain_guard", "passed": true, "zero_escape_spellable_all_forms": true, "cases_tested": 16, "all_out_of_domain_cases_exact_parity": true} |

## Reproduce

```sh
python -B replay.py check                    # Read-only verification (never modifies tracked files)
python -B replay.py check --report /tmp/r.json  # Write volatile receipt to an explicit path
python -B replay.py all                      # Re-run witness, transfer, dev_gate, and rebuild reports (dict64 frozen)
```
