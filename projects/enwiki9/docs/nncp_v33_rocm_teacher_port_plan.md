# NNCP v3.3 ROCm teacher port

Status: authorized source-level observation infrastructure; zero score credit.

## Established antecedent

The Radeon 8060S (`gfx1151`) executes AMD PyTorch 2.11/ROCm 7.13. The published
NNCP v2 PyTorch codec was modernized only by replacing the removed deterministic
API and changing Adam beta1 from integer `0` to floating `0.0`. Its 39,238,141
parameter model compressed and independently decompressed a 38,315-symbol
stream. Both the preprocessed stream and 65,536 raw bytes matched SHA-256.

ZLUDA is closed for this application. The shipped LibNC CUDA module contains
NVIDIA SASS ELF images and no PTX; ZLUDA reached `cuModuleLoadData` but could not
resolve `cu_memcpy2d_u8`. Do not install more CUDA shims or tune ZLUDA.

## Frozen v3.3 architecture target

Match the profile encoded in official `nncp.c`:

- 20 Transformer layers;
- model width 1024, 8 heads, key/value width 128;
- feed-forward width 3072 with GEGLU;
- learned relative-position dimension 320; rotary position embeddings disabled;
- recurrent memory 256 and segment length 64;
- untied input/output embeddings;
- per-layer learned `w_r[128,320,8]` relative-position tables and shared
  `b_r[320,8]` relative bias; exact padding and `rel_shift` parity required;
- pre-normalization, final normalization, and RMS normalization;
- BF16 parameters/activations with deterministic FP32 reductions where needed;
- dropout and attention dropout 0.19;
- Adam beta1 0, beta2 0.9999, epsilon 1e-8, gradient clip 0.05;
- v3.3 block, learning-rate, and retraining schedules.

## Gates

1. **Architecture gate:** exact tensor shapes, parameter count, causal mask,
   state dimensions, schedule points, and serialized configuration match the C
   profile. No corpus claim.
2. **Execution gate:** deterministic 64-symbol encode twice on ROCm without
   exceeding decimal 10 GB process-tree RSS for the bounded batch-1 observer.
3. **Distribution gate:** on identical symbols and declared initialization,
   compare every normalized 336-way distribution with a CPU LibNC observation.
   Separate expected RNG/numeric differences from structural errors.
4. **Headroom gate:** only after structural agreement, trace chronological
   development and holdout. Teacher advantage must exceed 3,000 B/M before any
   student is trained.
5. **Student gate:** freeze 64 KiB then 128 KiB integer students. Require exact
   package-adjusted recovery sufficient for the 108,000,000 target and require a
   matched hard-label control.

No WRT transfer, full-corpus run, 256 KiB student, or score credit is authorized
before these gates pass.
