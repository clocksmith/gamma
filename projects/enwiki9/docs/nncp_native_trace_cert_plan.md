# NNCP native trace and mature-headroom certificate

Status: authorized observation infrastructure; zero score credit; execution
blocked on this host because no NVIDIA CUDA device or `libcuda.so.1` is
available.

## Decision

Teacher-quotient compilation is the primary new-information lane. The teacher
must be the official NNCP v3.3 application linked to the unmodified shipped
`libnc.so` and `libnc_cuda.so` on one frozen NVIDIA system. The ROCm/PyTorch
online-update replica is retired as a teacher: its first update did not preserve
LibNC semantics.

The immutable source object is:

```text
nncp-2024-06-05.tar.gz
sha256 7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119
```

The locally extracted binary objects currently hash as:

```text
nncp          c3f6ee27f5ac69b58b3fc3d487d18fb2ef949f6eb197d6e709a972d80a65f34c
libnc.so      1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e
libnc_cuda.so ea9ee53d217a673e8547dddbfe8253b9c9ea4ec18ad86c7bd939ac2572f7999e
```

These hashes identify the local copy only. A decisive receipt binds the
materialized executable and every runtime library on the NVIDIA host.

## Important coder correction

NNCP does not pass a normalized 336-way integer frequency vector to its range
coder. `write_sym` recursively splits the floating output table and calls
`put_bit` with one clamped 15-bit integer probability for each branch on the
true symbol's path:

```text
prob0 = clamp(lrintf(left_mass * 32768 / active_mass), 1, 32767)
```

Therefore the authoritative Level A trace contains the exact integer branch
probabilities consumed by `put_bit`. A Level B record may additionally contain
all 335 integer branch probabilities in the deterministic binary split tree.
Those full-tree values are observation-only derived values, not a fictional
native 336-way integer interface.

## Native trace contract

The observer is materialized only from the immutable tarball by:

```text
tools/materialize_nncp_native_trace_observer.py
```

The runner and verifier are:

```text
tools/run_nncp_native_trace_cert.py
tools/verify_nncp_native_trace.py
```

Every symbol row records:

```text
execution ordinal
coder bit-count diagnostic before and after
physically emitted coder bytes before and after
true symbol and vocabulary size
exact consumed branch probabilities and branch bits
optional complete derived split tree
```

At predeclared completed-symbol checkpoints, the observer clones the arithmetic
coder, finalizes only the clone into a discard sink, and records exact
hypothetical archive bits and bytes. The live coder and teacher state remain
unchanged. Physically emitted bytes remain diagnostics; only shadow-finalized
checkpoint totals may enter exact boundary ledgers.

The exact symbol-to-raw mapping remains a separate hash-bound artifact produced
by the already passing symbol-map gate. Frozen raw windows are converted to
symbol windows through that map before the teacher run.

The conversion tool is:

```text
tools/nncp_native_window_manifest.py
```

It accepts only a passing, hash-bound map receipt. A raw boundary is legal only
when no symbol interval crosses it. The completed-symbol cut includes symbols
whose raw start is strictly before the boundary; this includes zero-output
controls belonging to a prefix event and excludes zero-output controls at the
start of the future side. The output supplies the exact `--full-windows` and
`--checkpoints` arguments for the native runner.

The existing opening-1M map proves the mapping machinery but cannot bind mature
windows or the published teacher because it uses an opening-scope dictionary.
A mature manifest requires one map built from the frozen full-corpus dictionary
and transformed stream, covering at least the 100M raw boundary.

Level A records consumed branches for all symbols. Level B records complete
derived trees only inside predeclared continuous-state symbol windows
corresponding to:

```text
opening 1M raw
9M-10M raw
49M-50M raw
99M-100M raw
```

The teacher starts at byte zero. No mature window may be reached by resetting
model, optimizer, preprocessor, or coder state.

## Identity gate

All conditions are mandatory:

```text
trace-off archive SHA-256 == trace-on archive SHA-256
trace-off decode SHA-256  == original raw SHA-256
trace-on decode SHA-256   == original raw SHA-256
all recorded branch probabilities are in [1, 32767]
every branch path terminates at the recorded true symbol
full-tree path equals the consumed path whenever Level B is present
coder counts are monotone and emitted-byte counts are monotone
source, patch, binary, LibNC, CUDA, driver, GPU, command, input, map hashed
```

The published command is retained as the full-run reference:

```text
./nncp --cuda --profile enwik9 --preprocess 16384,512 c enwik9 out.bin
```

Prepared-stream runs must use the exact full-corpus dictionary and transformed
symbol stream, both bound to the symbol-map receipt. A prefix-trained
dictionary is not interchangeable with the published teacher.

## Mature-headroom certificate

`NNCP-MATURE-HEADROOM-CERT` compares native NNCP and the exact source-bound
Gamma parent on identical raw boundaries and continuous prefixes. It reports
cumulative and marginal archive bytes, package bytes, startup debt, and mature
gain.

The hardware-independent decision tool is:

```text
tools/nncp_mature_headroom_cert.py
```

It consumes `nncp_native_boundary_ledger_v1`,
`gamma_boundary_ledger_v1`, and a passing `nncp_native_trace_cert_v1`
identity receipt. Any input hash, population, raw-boundary, continuous-state,
or window-set mismatch fails closed.

Authorization requires:

```text
native teacher advantage >= 3,000 B/M on at least two mature windows
cumulative 100M teacher advantage > 0
native trace identity passes
same raw population and continuous state
```

Failure closes teacher compilation before a student is built.

## Quotient budget and student boundary

Only after mature headroom passes may `QUOTIENT-BUDGET-CERT` test whether a
64 KiB or 128 KiB decoder-visible state machine can retain target-bearing
teacher gain. Teacher hidden states, gradients, future symbols, untransmitted
page labels, and offline block identities are forbidden.

The first constructive family, if authorized, is `QPDFA-336`: a deterministic
quotient state, variable-order suffix fallback, shared distribution
prototypes, sparse integer residuals, explicit frequent-symbol transitions,
and a default transition. Selection is by exact arithmetic bytes plus complete
package bytes, not KL divergence.

No student, WRT transfer, full-corpus Gamma run, or score claim is authorized
by this plan.

## External facts

- LibNC documents fixed-system determinism, CUDA-specific execution, and
  non-identity between CPU and GPU results:
  <https://bellard.org/libnc/libnc.html>
- NNCP publishes the 106,632,363-byte enwik9 archive and the reference command:
  <https://bellard.org/nncp/>
- Weighted-automata distillation is supporting methodology, not evidence that
  the required quotient exists:
  <https://arxiv.org/abs/2009.13101>
