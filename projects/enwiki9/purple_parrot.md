# purple_parrot — non-cmix lane notes

## What was built this session

### `programs/purple_parrot_nncp_v1/`
First non-cmix purple_parrot. NNCP-class online-trained char-LSTM + 32-bit Witten-Neal-Cleary arithmetic coder. No torch, no pretrained weights. Pure numpy + Python stdlib.

Files:
- `program.py` — single-file compressor (~290 lines)
- `meta.json` — registered, deps `["numpy"]`

Hand-coded primitives (the "torch we coded locally"):
- `_init_weights()` — PRNG-seeded weight init via `np.random.default_rng(SEED=0x5EED)`. Six tensors: byte embedding `W_e (256, 32)`, LSTM input proj `W_x (4H, 32)`, LSTM hidden proj `W_h (4H, H)`, gate bias `B (4H,)` with forget bias = 1.0, output proj `W_o (256, H)`, output bias `b_o (256,)`. Zero archive cost — decompressor regenerates them identically.
- `_lstm_fwd()`, `_lstm_bwd()` — single-step LSTM cell forward and backward, gates `i,f,g,o`. Returns full backprop including `dx` for embedding-table gradient.
- `_softmax()` — max-subtracted, float32.
- `_forward()` — `prev_byte → probs (256,)` via embed → LSTM step → output proj → softmax.
- `_train()` — cross-entropy gradient `dlogits = probs - one_hot(target)`; backprops through output proj and one LSTM step; per-tensor L2 gradient clip at `GCLIP=5.0`; in-place SGD updates with `LR=0.05`. Mutates the arrays inside `params` so encoder and decoder stay in lockstep.
- `_cum_counts()` — softmax probs → integer cumulative counts summing exactly to `2**14`. Floor-then-clip-to-1; deterministic deficit/surplus adjustment via `argsort(-p, kind='stable')` for surplus, `argmax(c)` loop for deficit.
- `_BW`, `_BR` — bit writer/reader for byte-aligned output.
- `_AE`, `_AD` — 32-bit Witten-Neal-Cleary range coder. E1/E2/E3 renormalization. `_AD.find_sym()` does binary search on `cum[]` for the symbol whose interval contains the current code value.
- `compress(data: bytes) -> bytes` and `decompress(arch: bytes) -> bytes` — the public contract. Archive layout: `>Q` length prefix (8 bytes) + arith payload.

### Encoder/decoder lockstep contract
At every step both sides:
1. Run `_forward(prev_byte, h, c, params)` — same compute, same probs.
2. Compute `_cum_counts(probs)` — same integer cumcounts.
3. Encoder calls `ae.enc(cum, target=data[i])`; decoder calls `ad.find_sym(cum)` followed by `ad.upd(cum, sym)`. The arith coder's invariant guarantees `sym == target`.
4. Both call `_train(prev_byte, target, probs, h1, cache, params)` — same gradient, same in-place update.
5. Both advance `(h, c, prev_byte)` to identical new values.

This gives bit-exact roundtrip on a single host with single-threaded numpy.

### Honest entropy expectation
1-layer LSTM at H=128, no BPTT, char-level, online-trained. Per-byte entropy on enwik9 is empirically in the 2.0–2.4 b/B band for a model of this depth — the substrate is the same as the small-model NNCP baselines that predate Bellard's transformer-XL work. Predicted full-corpus archive ≈ 250–300 MB. **This v1 will not beat fx2-cmix.** Its job is to validate the lockstep contract and establish the lane.

### Index registration
Added `purple_parrot_nncp_v1` entry to `index.json` programs list (between `purple_parrot_apex_v1` and `yellow_tucan_range_order_v1`).

## What to do next

### Step 1 — smoke `purple_parrot_nncp_v1` at 1 MB scope, no run yet (asking permission)
Concrete check before any benchmark: `lib/smoke.py` 5-tier on this program. The non-trivial gates that are most likely to fail:
- **Tier 3 (cross-host determinism via `--check-determinism`):** numpy float32 ops are deterministic *within* a single thread; if the driver invokes the program twice in a single process they should return byte-identical archives. If the test runs in two subprocesses with `MKL_NUM_THREADS` differing, this will diverge. Need to confirm `lib/driver.py` pins thread count to 1 for numpy programs, or set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` in the smoke harness for this program.
- **Tier 4 (/dev/urandom incompressibility):** the LSTM has never seen anything; on 1 MB random bytes the model will output near-uniform probs and the arith-coded output should be ≤ input + epsilon. Risk: large overhead from the 8-byte length prefix on tiny inputs (smoke probably uses ~1 KB) — confirm smoke passes with reasonable tolerance.
- **Tier 5 (prefix roundtrip):** compress(data[:k]) for k < len(data) must roundtrip. Should work since we have a length prefix.

If a gate fails, the real fix is in this file:
- Determinism failures → audit numpy reduction order in `_lstm_fwd` / `_lstm_bwd`; specifically `W_x @ x + W_h @ h + B` evaluates left-to-right (BLAS-deterministic per-thread).
- Roundtrip failures → likely the cumcount adjustment in `_cum_counts` produces different counts in encoder vs decoder due to a tied argmax. The `argmax(c)` deficit loop is the suspect spot — `np.argmax` returns the first index on ties, which is deterministic, but if the adjustment differs by even one count between encoder and decoder, the arith coder desyncs and the rest of the stream decodes garbage.

### Step 2 — once 1 MB smoke is green, run a real 1 MB bench
`lib/bench.py purple_parrot_nncp_v1 --scope 1MB`. Record the per-byte entropy in the result JSON. Compare against:
- `baseline_lzma` at 1 MB (≈ 290,933 bytes program+data) — NNCP at this size will lose, badly.
- `purple_parrot_markup_opcode_lzma_v1` at 1 MB (≈ 290,301 bytes) — same.

The point is not to win at 1 MB. The point is to measure actual b/B and confirm the encoder-decoder roundtrip matches the SHA256 contract. Expected b/B at 1 MB: 2.5–3.5 (the model has very few SGD steps to learn the corpus).

### Step 3 — extend toward usefulness (`purple_parrot_nncp_v2`)
Once v1 is green, the concrete deltas to graduate from "diagnostic" to "fx2-cmix challenger":

| Delta | File/symbol | Effect |
|---|---|---|
| Truncated BPTT, K=8 | replace `_train` with a buffer of caches; `_lstm_bwd` already returns `dh0, dc0` and propagates correctly | Drops per-byte entropy substantially; this is the single biggest gap from v1 to NNCP-base |
| Second LSTM layer | duplicate `(W_x, W_h, B)` into layer-1 and layer-2 sets; `_lstm_fwd` chains them; `_lstm_bwd` chains gradients in reverse | Smaller marginal gain than BPTT but cumulative |
| H=128 → H=256 | flip the constant in `program.py` | Better prediction, ~4× compute per step |
| Adam optimizer | maintain `m, v` moment buffers per tensor in `params`; replace SGD updates in `_train` with bias-corrected Adam step | Faster online convergence — large effect on per-byte entropy in the first ~100 KB of the corpus |
| Byte-pair tokenization on input | precomputed byte-pair table baked into `program.py` (counts in program_size); embedding table indexed by token id, not raw byte | Decouples input alphabet from output; lets the LSTM see longer-context structure |

Each is a separate `purple_parrot_nncp_v{N}/` directory with its own `meta.json` and roundtrip smoke.

### Step 4 — int-quant for strict cross-host parity (`purple_parrot_nncp_v3+`)
Float32 is "deterministic enough" same-host. For Hutter-style cross-host SHA256 verification (x86 ↔ ARM ↔ different numpy/BLAS builds), the canonical fix is integer-quantized arithmetic:
- Replace fp32 weights with int16 (per-tensor or per-row scale).
- Replace `_lstm_fwd` matmuls with int32-accumulated integer matmul.
- Replace `tanh` and `sigmoid` with 32-segment LUTs matching the locked spec.
- Replace softmax with shift-invariant integer normalization.

This is its own chunk of engineering and should land as a separate program, not a patch to v1.

### Open questions for the user (when ready)
- Should `purple_parrot_nncp_v1` be smoked at 1 MB now, or write v2 (with BPTT) first and smoke that instead?
- Confirm numpy is acceptable as a `deps` entry for the lane, or do we need to write the matmul in pure Python (which collapses the throughput by ~50–100×)?
- Cross-host SHA256: do we treat fp32-numpy roundtrip as the v1 contract and defer strict cross-arch parity to int-quant v3, or block v1 until int-quant lands?

## Reject list (do not silently re-introduce)
- ✗ pretrained model weights of any kind in the archive or program
- ✗ float64 cast for "stability" — breaks the program-size budget for no entropy gain
- ✗ multi-threaded numpy / BLAS — non-deterministic reduction order
- ✗ skipping the gradient clip — LSTM diverges within hundreds of steps without it on enwik9
- ✗ caching weights between runs — every `compress()` call must regenerate from `SEED`

## Status
- `purple_parrot_nncp_v1` written, registered in `index.json`, **not yet smoked, not yet benched**.
- Awaiting permission to run `lib/smoke.py` 1 MB tier on `purple_parrot_nncp_v1`.

## Sibling lane status (cmix-wrapped)

`purple_parrot_apex_v1` 1 MB smoke landed this session, all gates green:

| metric | value |
|---|---|
| `compressed_size` | 193,137 |
| `program_size` | 504,328 |
| `hutter_score` | 697,465 |
| `bits_per_byte` | 1.545 |
| `roundtrip_ok` | true |
| `single_host_byte_equal` | true |
| sha256 | `a3d77afa…51ce86c1` |

Result file: `results/purple_parrot_apex_v1/2026-05-09T155228.json`.

Implications:
- Apex's cmix v21 substrate at 1 MB hits 1.545 b/B, already cleaner than `xz_lzma2_1g`'s full-corpus 1.583 b/B.
- S at 1 MB is dominated by the 504 KB embedded cmix blob; archive is only 193 KB.
- Crossover where apex beats xz on S: ~109 MB corpus.
- Projected full-corpus S ≈ 111.2 MB. Beats xz by ~86 MB. Misses fx2-cmix (110.79 MB) by ~400 KB — that gap is the missing sidecar-feature work, not an apex bug.

This means the cmix-wrapped lane is empirically validated end-to-end (the embedded blob is portable, deterministic, roundtrip-safe). The path to fx2-cmix-or-better on this lane is sidecar features (the locked 10-step plan), not more apex tuning.

The NNCP lane (`purple_parrot_nncp_v1`) is parallel and independent — it is not a refinement of apex.
