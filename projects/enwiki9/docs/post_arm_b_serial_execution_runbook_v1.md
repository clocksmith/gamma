# Post-Arm-B Serial Execution Runbook v1

## Global invariant

Execute exactly one heavy build, compressor, decompressor, or NNCP arithmetic
gate at a time. Before every command, require no live `cmix`, `cmix_orig`,
`archive9`, NNCP gate, or adaptive worker process. Never reuse an active result
directory or `/dev/shm` for CMIX scratch.

## 1. Terminal external A/B audit

Do not invoke this command until the Arm B driver and complete process tree are
absent and its terminal receipt is durable:

```bash
python3 projects/enwiki9/tools/cmix_obias_source_full1g_ab_terminal_audit_v2.py
```

The audit may establish source-built A/B archive and payload identity plus exact
canonical inverse. It must separately record Arm B's process-RSS and tmpfs
resource failures. It grants zero Gamma compression or score credit.

## 2. Open NNCP probability-adjoint gate

Run alone after the A/B audit:

```bash
python3 projects/enwiki9/tools/run_with_rss_guard.py \
  --limit-kib 9765625 \
  --limit-mode tree \
  --official-decimal-limit-kib 9765625 \
  --guard-json projects/enwiki9/results/nncp_open_top_attention_value_transpose_64_q0_v1/guard.json \
  --label nncp-open-top-attention-value-transpose-64-q0-v1 \
  --phase diagnostic \
  --scratch-path projects/enwiki9/results/nncp_open_top_attention_value_transpose_64_q0_v1 \
  --temporary-disk-limit-bytes 100000000000 \
  -- \
  python3 projects/enwiki9/tools/nncp_open_top_attention_value_transpose_64_q0.py \
    --experiment projects/enwiki9/operations/adaptive/experiments/nncp_open_top_attention_value_transpose_64_q0_v1.json \
    --output projects/enwiki9/results/nncp_open_top_attention_value_transpose_64_q0_v1/decision.json
```

Frozen identities:

```text
runner SHA-256      5f8d979a9930df07af9de7d062a775bfac327aa54c38dcb295adcbf8a0008865
experiment SHA-256  d7a4a4ce592be614fe1a44e44545e0c551a45bc5f03e512f5dc05ec97ae06931
population          5,242,880 BF16 probability-adjoint words
compression credit  0
```

A pass proves only `dP = dAttended * V^T` for the frozen population and controls.
It does not prove a complete open NNCP backward pass or any archive gain.

### Held NNCP score-adjoint source oracle

After an exact dP decision, the following source oracle is eligible to be
enqueued under the adaptive runner, still alone and under the same guards. It
must not be invoked as an unbound direct command because its runner requires
the job's experiment and candidate-revision environment bindings.

```text
candidate              nncp_libnc_top_attention_softmax_input_adjoint_oracle_64_q0_v1
candidate tree          b5f1f7590ea02f7cfdcbe7d62bdb38ad1d0f5bb99522093d0d3298664bda278c
revision receipt SHA    24803a0585fdf71942938a783ed6281edad612070b6d0c5a97523f1fceff841f
experiment v2 SHA       af46a8014fb67ec6b1f31d4e3fe74cd92d2953e6a8472bdbdeaf2a07de84db8e
runner SHA              988ed38ab70fcfb1c651e24cf2f5503ad6d43f422ba0fef5fb5ef846cef69dc7
probe SHA               81aa38a12cc4ea15321c8a5dd34653522da0ad4767a117fecd6d05b64ede2bc5
compression credit      0
```

A pass yields only the complete source `score_input` and `score_adjoint`
oracle populations. It authorizes a separately frozen open softmax-backward
gate for `dS = P * (dP - sum(P*dP))`; it does not prove that arithmetic.

The LibNC-free scalar reference is prepared but not materialized:

```text
kernel SHA-256          c8a403d96016a00ed653d63717bfbd5baa6bc5aeaf7d379fc556673502184ad5
runner SHA-256          9603e1b92663f1d0712ca416a408115aae828ab34b74036cee9047d8e0bdf71e
contract SHA-256        2ea69a90836195dadcd1307435dd1ff5a58dd7ac963ecb3c06585c835f9c6207
experiment              absent until source score-adjoint terminal pass
compression credit      0
```

Do not compile or run it before the source oracle passes. Then freeze a new
experiment binding the actual `P`, exact open `dP`, source `dS`, candidate
revision, compiler, flags, guards, controls, and output paths before execution.

## 3. Disk-backed PPM0 resource diagnostic

Run the clean control, PPM0 treatment, and joint decision serially:

```bash
GAMMA_ENWIK9_DISK_SCRATCH=/home/x/enwiki9-scratch \
python3 projects/enwiki9/tools/cmix_obias_ppm_clean_250k_disk_q0_v1.py
GAMMA_ENWIK9_DISK_SCRATCH=/home/x/enwiki9-scratch \
python3 projects/enwiki9/tools/cmix_obias_ppm_always_purge_250k_disk_q0_v2.py
python3 projects/enwiki9/tools/cmix_obias_ppm_disk_joint_q0_v3.py
```

Frozen identities:

```text
clean runner SHA-256      26c5858bcd036b574618ddb367ed565b948045e2dd50652535695af00e723751
PPM0 runner SHA-256       1ca9f2d978b45a1ff30b638ffe3ddbb2fe9e68070f2b59de194048ebe4173c39
joint evaluator SHA-256   dbc171b46b55acd3514df925d8908c1922739ac1e699616db1ca28cd0248b8e1
experiment SHA-256        4335c88ebafc7e7487d463d0816ba01b98ecf14e52a8987e0a2fd2e159037079
compression credit        0
```

Require exact payload identity against the matched clean control,
non-memory-backed scratch, process-tree RSS at most 9,765,625 KiB, allocated
scratch at most 100,000,000,000 bytes, exact inverse, and complete cleanup. PPM0
changes residency only and receives zero compression credit.

## 4. Midpoint v3 diagnostic

Only if step 3 passes, execute C/P/K/O/R/D/S serially, never concurrently:

```bash
for arm in C P K O R D S; do
  GAMMA_ENWIK9_DISK_SCRATCH=/home/x/enwiki9-scratch \
  python3 projects/enwiki9/tools/cmix_obias_bithead_delta_midas512_disk_q0_v5.py \
    --arm "$arm" --ppm-always-purge || exit $?
done
python3 projects/enwiki9/tools/cmix_obias_bithead_delta_midas512_joint_disk_q0_v5.py \
  --ppm-always-purge
```

This evaluates the sealed midpoint algorithm through corrected disk runner
infrastructure. Its joint decision remains zero-credit opening evidence.

## 5. Online FTRL v5 diagnostic

Execute C/P/K/O/R/D/S serially:

```bash
for arm in C P K O R D S; do
  GAMMA_ENWIK9_DISK_SCRATCH=/home/x/enwiki9-scratch \
  python3 projects/enwiki9/tools/cmix_obias_bithead_ftrl512_disk_q0_v5.py \
    --arm "$arm" --ppm-always-purge || exit $?
done
python3 projects/enwiki9/tools/cmix_obias_bithead_ftrl512_joint_disk_q0_v7.py \
  --ppm-always-purge
```

The v7 decision reads unchanged v5 arm artifacts and requires durable payload
bytes, SHA-256 and direct byte identity for C=P and P=K, live K shadow
arithmetic, plus probability, recurrent-state, adapter, maximum, and finite
synchronization across encode, repeat, and bare decode.

### Held Scalar-MIDAS64 sibling

`cmix_obias_scalar_midas64_ppm0_q0_v1` is rejected before execution because it
did not bind the parent's byte-zero cold start or midpoint/reset order relative
to `Advance`. It has no scientific verdict and no compression credit.

The corrected proposal is held at the development boundary:

```text
proposal                cmix_obias_scalar_midas64_ppm0_q0_v2
contract SHA-256         c18dff2db137575448d4875db549a038c98c015da6c109bdb7002dd6516164a5
experiment SHA-256       26422998d140c54c90d4f8cc7b20529d64973cff8ac018ff8e5e7097334bb008
expected savings         0 (unmeasured)
maximum package bytes    65,536
```

Do not develop or enqueue v2 until the disk-backed PPM0 joint decision passes.
Its implementation must preserve byte zero's all-zero initial prior, select
the byte-32 gate before `Advance(byte31,p32)`, and restore the byte-64 gate
before `Advance(byte63,p64)`.

## 6. Promotion boundary

Do not promote from projected log loss, equal archive size, one successful
encode, or partial controls. Promotion requires actual smaller payload bytes,
exact inverse, deterministic repeat, complete package accounting, disk/RSS
compliance, cleanup, and D smaller than P/K/O/R/S.

The 10MB opening threshold is a 40,793-byte gross payload signal gate; package
debt is tracked separately. At the maximum 65,536-byte incremental package,
full-corpus archive size must be at most 104,442,981 bytes to keep the complete
counted total at or below 105,000,000 bytes.
