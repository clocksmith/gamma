# 256one typed composition integration on 128

The separate `algsolve.composition_bridge` exposes the actual frozen typed-program
v2 language and the previously measured original-checkpoint GPU guard. Existing
editor bridge, judge, codecs, and runtime-bound catalog files are unchanged.
The default stored-answer path uses the new dependency-bound 2,501-entry catalog.
The rejected balanced-loss checkpoint is never loaded by this bridge.

The 256one two-button workspace now offers three original typed-language examples,
a complete operation/effect/recipe description, editable typed JSON, explicit
sandbox checking, autonomous composition from the current problem, and explicit
insertion of example-passed Python. Neither checking nor composition inserts code
automatically. Edits invalidate results; asynchronous replies bind problem revision,
complete request bytes and the current graph. Seven/eight-bit encodings are unchanged.

`typed_check` validates JSON graph structure, bindings, types, resources and codec,
then deterministically assembles the existing bounded interpreter and checks only
public examples in the existing isolated judge. `compose` uses one parallel model
prediction plus the frozen structural/literal guard; it does not retrieve a known
answer, generate autoregressive source or learn online. Explicit protected slugs
are refused. GPU absence or artifact drift fails closed. Setup is separate from
the two-second warm decision budget; an eight-second cold request is not a
subsecond interactive response. Results state that unfamiliar/nearby semantics
remain unqualified and public examples are not independent correctness.

Desktop/mobile browser checks passed: 13 tests covering existing retrieval,
composition insertion, stale replies and all three real paired-sandbox examples.
Five focused backend tests and two subtests passed. A real original-model
height-checker request returned an example-passed graph in 8.295 seconds including
cold setup, with a 0.105-second measured warm route. A newly dependency-qualified
stored answer also passed through the actual bridge with catalog approval.
These are integration checks on already consumed/qualified inputs, not a fresh
model benchmark. [Live receipt](live-receipt.json) records the results.

Start on128 with the existing local runtime:

```sh
PYTHONPATH=projects/algorithm_solver HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
.venv_rocm/bin/python -m algsolve.composition_bridge
```

The listener remains `127.0.0.1:8875`, with the same approved origins, explicit
pairing, one job at a time, request/result hash binding, cancellation and deadline.
Use the existing SSH loopback forward from another browsing computer. No LAN
listener, public runner, authentication bypass or security policy change was added.

The initial integration receipt is retained under `initial-integration/`. The final
route validates raw graph diagnostics without spending an extra public execution;
all live inference and diagnostics are charged to the guarded route.

Exact manifest-bound SortedList sources also passed the ordinary editor Run action
after insertion. Modified source received the original runtime and failed closed;
no arbitrary program gained the optional dependency.
