# Explicit numerical-profile successor (not an execution permit)

This prospective owner preserves the existing paired predictor, model, precision,
prompt, ranking, service, data and admission semantics. `owner.build` now passes
the declared batch size and threads to the existing lazy CPU encoder instead of
hardcoding batch four. A future frozen caller must supply `numerical_profile`;
the actual encoder identity must match before encoding, after each call, and before each cache chunk read/write.

The profile binds model/runtime manifests, native Python, encoder adapter,
batch size, threads/inter-op threads, CPU/float32, token limit, padding, pooling
and query instruction. Loader readiness is not part of the numerical identity.
The resulting profile-aware vector identity flows through the existing cache,
ranking and provenance checks. Same-profile exact caches remain resumable under
their original authorization rules; different profiles and unprofiled caches
are rejected. This does not assert that every batch change alters vectors.

The original `contract-clause-paired-runner-v1` freeze, its failed headroom
preflight, and all existing caches remain unchanged. No historical mismatch or
invalid result has been demonstrated. The successor is a construction component,
not a separately approved launcher: no new run freeze, claims or execution
permission are created here. A future run needs fresh profile-bound cache paths,
complete code/data pins, independent review and the existing resource approval.

## Resource review outcome

The proposed batch-two / 3.75 GiB summed-RSS / 4.25 GiB initial-headroom profile
was rejected before launch. The earlier actual batch-two synthetic smoke
(`native-cpu-adapter-smoke-v1.json`, SHA256
`144339854cfd8c6d1961b964c5d1f0e733a432dfd11e83599379afcf592d17fb`)
reported 4,041,039,872 bytes peak child RSS, already 14,508,032 bytes above that
proposed total-owned limit, excluding its supervisor. Smaller batches do not
establish a lower model-loading or allocator peak. The existing 4.75 GiB
preflight guard remains unchanged. The existing 50 ms summed-RSS watchdog is
sampled enforcement with possible overshoot, not a kernel allocation cap or
a guarantee against unrelated platform memory pressure.

## Focused evidence

Eight synthetic tests pass: explicit lazy factory configuration; batch/thread
identity separation; same-profile cache restoration; cross-profile and legacy
cache rejection; pre-encoding and cached-restoration drift rejection; invalid configuration and exact
profile mismatch; query provenance and profile-aware vector identity. Tests
use fake vectors and the actual cache/binding owners, no torch import or model
run. No recognition improvement, qualification or milestone completion follows.

Run from the repository root:

```sh
PYTHONPATH=. python3 -m unittest discover \
  -s projects/algorithm_solver/catalogue/contract-clause-paired-runner-v2 \
  -p 'test_*.py' -v
```
