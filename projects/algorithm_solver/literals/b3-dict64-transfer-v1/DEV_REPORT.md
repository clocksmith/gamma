# B3 Development Report: One Transferable 64-Entry Dictionary

## Decisions (Reported Separately)

- **matched80 Witness Decision:** `PASS`
- **Dev Transfer Decision (disjoint 83 spent JS problems):** `PASS`
- **dev_gate Verification:** `PASS` (9/9 gates & negative controls passed)

> Witness (fit on `matched80`) and dev transfer (frozen evaluation on disjoint spent JS problems) are strictly separated decisions. No sealed/protected clusters were opened, no packages were installed, and no GPU/network compute was used.

## 1. Cohorts & Baseline Rank Pins

- **matched80:** 80 JS programs, 8412 frozen behavior tests, verified byte-for-byte against Git pin `59ff04415ff2afd04ff2ed451340f4f02852bf18` with 80/80 trailing newlines preserved.
  - Raw `canonical` baseline (40467 B): alphabet=92, exact unrestricted rank min=79, exact witnessed rank min=92.
  - Raw `compact` baseline (18542 B): alphabet=92, exact unrestricted rank min=79, exact witnessed rank min=92.
  - Raw `original` baseline (57236 B): alphabet=93.
- **Separate Spent Dev Transfer Cohort:** 83 disjoint JS problems (4878 frozen cases, 50689 raw bytes) from `continuation-a-20261028-v1, continuation-d-20261028-v1, continuation-f-20261028-v1, continuation-h-20261028-v1, continuation-j-20261028-v1, continuation-l-20261028-v1, continuation-n-20261028-v1, continuation-o-20261028-v1`, programmatically verified 0 overlap with `matched80` and 0 overlap with reserved/protected IDs.

## 2. All 4 Required Arms on `matched80`

| Arm | Source / Policy | Alphabet / Slots | Coverage (0-esc) | Entries | Package Bits (excl. dec) | Decoder Bits | Complete Bits | Max Step Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Arm 1a (Raw flat @64) | Raw `canonical` (\n kept) | 92 chars / 0 learned | 64/80 (infeasible) | 64 | n/a | n/a | n/a | 1.0000x |
| Arm 1b (Raw flat @256) | Raw `canonical` (\n kept) | 92 chars / 164 learned | 80/80 | 256 | 72112 (Huff) / 74448 (F8) | 0 (ref) | 72112 | 1.0000x |
| Arm 2 (Fixed canonical @64) | Frozen rewriter + flat tiler | 37 singles / 27 multi | 80/80 (0 esc) | 64 | 73584 (B3H1) / 85584 (F6) | 9840 | 83424 | <=1.1000x |
| **Arm 3 (Joint canonical @64)** | **Joint rewrite + witnessed dict64** | **37 singles / 27 multi** | **80/80 (0 esc)** | **64** | **71640 (B3H1) / 83208 (F6)** | **9840** | **81480** | **1.0331x** |
| Arm 4 (BPE-256 `canonical`) | Raw `canonical` BPE-256 (\n kept) | 92 base + 164 merges | 80/80 | 256 | 82784 (Huff) / 90528 (F8) | 0 (free) | 82784 | 1.0000x |
| Arm 4 (BPE-256 `original`) | Raw `original` BPE-256 (\n kept) | 93 base + 163 merges | 80/80 | 256 | 165872 (Huff) / 180504 (F8) | 0 (free) | 165872 | 1.0000x |
| Arm 4 (BPE-256 `compact`*) | Pre-minified `compact` BPE-256 | 92 base + 164 merges | 80/80 | 256 | 59560 (Huff) / 64392 (F8) | 0 (free) | 59560 | 1.0000x |

*Note on Arm 4 controls: `canonical` (40,467 B) and `original` (57,236 B) are unminified raw JS controls (with `canonical` matching the exact 79 unrestricted / 92 witnessed minima of `witness-coverage-v1`); `compact` (18,542 B) is already AST-minified by `scale-v2/generate.cjs` and is reported transparently as a pre-minified reference ceiling. Arm 3's charged witness decoder (`b3_witness_decoder.py`) is 1230 B (9840 bits); charging the full transfer-capable decoder (`b3_ref_decoder.py`, 15608 bits) yields 87248 bits.

## 3. Dev Transfer Evaluation (Frozen Rewriter + Frozen 64-Entry Dictionary)

- **Coverage:** 72/83 accepted (86.8%), 11 refused and shipped via charged raw fallback (`frozen_matched80_bpe255_escape`).
- **Wrong acceptances:** `0` (strict requirement: `0`).
- **Single fixed canonical spellable:** 81/83.
- **B3 Transfer Complete Bits (including selector + fallback table + fallback stream + 15608-bit decoder):** `165496` bits (package excl. decoder: `149888` bits; raw-UTF8 fallback option: `175000` bits; frozen-BPE255 fallback option: `165496` bits).
- **Baselines on identical 83 raw transfer programs (50689 B):**
  - Frozen `matched80` BPE-255+escape (`canonical` fit, Huffman): `219656` bits (fixed-8: `277152` bits).
  - Frozen `matched80` BPE-255+escape (`original` fit, Huffman): `221056` bits.
  - In-domain dev-transfer BPE-256 (fit directly on transfer set, Huffman): `175656` bits (fixed-8: `194824` bits).

### Problem Family Transfer Breakdown (Every Uncovered Family Reported)

| Problem Family | Total | Accepted (0-esc) | Refused (Fallback) | Coverage |
| --- | ---: | ---: | ---: | ---: |
| `array_greedy_search_ds` | 6 | 6 | 0 | 100.0% |
| `general_algorithmic` | 15 | 12 | 3 | 80.0% |
| `geometry_matrix_graph` | 10 | 6 | 4 | 60.0% |
| `math_bitwise_combinatorics` | 19 | 18 | 1 | 94.7% |
| `string_window_sequence` | 33 | 30 | 3 | 90.9% |

- **Families with any refusal:** ['general_algorithmic', 'geometry_matrix_graph', 'math_bitwise_combinatorics', 'string_window_sequence']
- **Completely uncovered families (0 accepted):** []
- **Refusal reason counts:** `{"step_ceiling_exceeded": 9, "unspellable_zero_escape": 2}`
- **Top unspellable syntax/literal blockers:** `{" ": 1, "^": 1}`

## 4. Shared Spine Summary (`fidelity`, `complete_bits`, `measured_work`, `horizon` H*)

### Witness (`matched80`)
- **fidelity:** 80/80 covered (0 escapes), 8412/8412 frozen tests passed, 80/80 <= 1.1x steps (median=0.938093x, p95=1.001011x, max=1.033086x), independent decode=80/80, wrong_acceptances=0, changed_algorithms=0.
- **complete_bits:** `81480` bits (`header=2720`, `stream=68920`, `decoder=9840`, `hidden_helpers=0`, explicit hoisted constants inside stream=`14259` bits across 50 programs).
- **measured_work:** total wall=64.2107s (rewrite=0.5158s, arm2_build=5.6261s, arm3_selection=1.7992s, cand_verify=1.4331s, witness_reexec=0.6168s, decode=0.078846s, decode_p95=0.3532 ms/prog), peak RSS=145,915,904 B, measured steps=780,590 vs original 831,226 (agg ratio=0.939083x).
- **horizon H*:** vs Arm 4 `canonical` Huffman BPE-256 = `73` programs (36926.1 raw B); vs Arm 4 `original` Huffman BPE-256 = `11` programs; vs raw `canonical` UTF-8 = `4` programs.

### Dev Transfer (Disjoint 83 Spent JS Problems)
- **fidelity:** 72/83 accepted (0 escapes), 11 refused -> charged raw fallback, wrong_acceptances=0, accepted step ratio median=1.0x / p95=1.038126x / max=1.064563x.
- **complete_bits:** `165496` bits (`primary_header=2720`, `fallback_total=31880`, `covered_stream=115251`, `decoder=15608`).
- **measured_work:** total wall=10.6412s (rewrite=0.4407s, selection=0.0951s, verify=2.0387s, decode=0.042556s, decode_p95=0.2763 ms/prog, reexec=1.916s), peak RSS=76,611,584 B, measured steps=32,158,196 vs original 31,946,707 on accepted programs.
- **horizon H*:** vs frozen `matched80` BPE-255 `canonical` Huffman = `24` programs; vs in-domain dev BPE-256 Huffman = `57` programs; vs raw UTF-8 = `7` programs.

## 5. Diagnostics: Rewrite Yield, Dictionary Utilization & Runtime Tails

- **Rewrite yield (`matched80`):** 423/423 rewrite candidates verified & step-compliant; raw canonical 40,467 B -> Arm 3 rewritten 23,751 B (ratio 0.5869x vs canonical, 0.415x vs original).
- **Dictionary utilization:** `matched80` uses 64/64 entries (100.0%); min multi-char fit support = 3 programs (>=2 enforced). On dev transfer, 62/64 entries are used (96.9%); unused on transfer: `[' in ', 'throw(']`.
- **Changed algorithms:** `0` across both cohorts (strictly semantics-preserving AST canonicalization).
- **Witness top-5 runtime-step ratios:** #1046=1.0331x, #9=1.0075x, #14=1.0031x, #3=1.0011x, #58=1.0010x
- **Transfer top-5 accepted runtime-step ratios:** #3836=1.0646x, #3934=1.0608x, #3625=1.0416x, #3742=1.0381x, #3820=1.0341x

## 6. `dev_gate` Verification & Mandatory Negative Controls

| Gate / Negative Control | Status | Detail |
| --- | --- | --- |
| `G1_matched80_pin_and_rank_baselines` | **PASS** | pin=59ff04415ff2, compact=79/92, canonical=79/92, trailing_nl=80/80 |
| `G2_witness_independent_decode_zero_escapes` | **PASS** | 80/80 exact match across independent_decode, b3_witness_decoder, b3_ref_decoder, and B3P1; 0 escapes |
| `G3_dict64_witnessed_eligibility` | **PASS** | entries=64<=64, witnessed_ok=True, errors=[] |
| `G4_witness_tests_and_step_ceiling` | **PASS** | programs=80/80, cases=8412/8412, step<=1.1x=80/80, max_ratio=1.0331 |
| `G5_witness_complete_bits_le_arm4_bpe256` | **PASS** | arm3_complete=81480 b (pkg=71640 + witness_dec=9840) <= arm4_canonical_huff=82784 b (fixed8=90528 b) & arm4_original_huff=165872 b; [pre-minified compact_huff=59560 b logged separately] |
| `G6_dev_transfer_frozen_fallback_zero_wrong_acceptances` | **PASS** | accepted=72/83, fallback_ok=11, wrong_acceptances=0, frozen_hash_ok=True |
| `NC1_hidden_helper_rejected` | **PASS** | {"name": "negative_control_1_hidden_helper", "passed": true, "subcheck_undeclared_free_helper_rejected": true, "subcheck_undeclared_reason": "undeclared_or_hidden_helper", "subcheck_injected_helper_rejected": true, "subcheck_injected_reason": "injected_hidden_helper_forbidden"} |
| `NC2_invalid_dict_id_rejected` | **PASS** | {"name": "negative_control_2_invalid_dict_id", "passed": true, "subcheck_b3p1_invalid_id_rejected": true, "subcheck_b3p1_error": "invalid dictionary ID 63 (vocab_len=5)", "subcheck_b3h1_over64_rejected_independent": true, "subcheck_b3h1_over64_rejected_ref_decoder": true, "subcheck_b3h1_error": "dictionary size 65 outside [1, 64]", "subcheck_b3h1_corrupt_huffman_rejected": true} |
| `NC3_step_ceiling_exceeded_rejected` | **PASS** | {"name": "negative_control_3_step_ceiling", "passed": true, "problem_id": 136, "all_outputs_correct": true, "original_steps": 3679, "slow_steps": 18232, "step_ratio": 4.9557, "rejected_by_1_1x_ceiling": true} |

## Reproduce

```sh
python replay.py check   # Verify frozen artifacts, independent decode, step verifier & negative controls
python replay.py all     # Re-run eval_dev, transfer_eval, dev_gate, and rebuild report
```
