# Explicit native continuation candidates

This directory adds separately authored JavaScript and Python class implementations
for 3709, 3815 and 3829. Official public GraphQL responses establish frontend IDs,
titles, constructor/method signatures and constraints. Only their hashes, URLs and
structured interface facts are retained here; full responses stay private.

The pre-source reference freeze binds direct abstract state models and contracts
before any candidate file was written. The score reference scans event pairs,
the auction reference scans all live bids, and the ride reference uses literal
FIFO lists. Candidates instead use prefix sums and binary search, lazy priority
queues, and cursor/deque queues with lazy cancellation. Expected values never
belong in a candidate packet. These are exposed development variants, not fresh
held-out problems or proof that no imported implementation exists elsewhere.

Each source contains its actual official native class. JavaScript additionally
exports the class as a property of the callable CommonJS `solve` export; Python
defines it at module scope. The separate `solve(operation_names, argument_lists)`
adapter constructs exactly one instance per trace and invokes the native methods.
Its result contains one null for construction, null for void methods, and each
method result in call order. Input trace arrays remain unchanged and returned
mutable containers are fresh. These local adapter effects do not assert that the
official problem requires a functional wrapper or treats a transcript as native
input.

Native ABI qualification requires a separately pinned observer that resolves the
declared class symbol, constructs it and dispatches its exact method allowlist
inside the existing isolation boundary. No class injection, free helper expansion
or fallback interface is authorized. The supplied static signature checks and
trace models do not substitute for this execution evidence. A future observer
must preserve state within a trace, create new state between traces, inspect full
typed results and input/alias effects, and keep expected outputs on the host.

`native_harness.py` and `native_harness.cjs` implement that direct dispatch route;
`native_protocol.py` owns argument-only packet construction and the host record
checks. They reuse the existing easy16 observation transport and existing judge,
not a new execution engine. `native-bindings.json` pins those external source
dependencies and the exact sandbox filenames. Only the candidate, native harness,
existing transport and argument packet may enter the child filesystem. The
references, case generators, contracts, checks and expected values stay on the
host. These files prepare a separately frozen route; they do not add it to any
global interface allowlist or authorize execution by merely importing a helper.

`oracles.py` validates complete official trace domains but limits its direct
reference work to 500 method calls. `cases.py` builds official examples and 48
deterministic development traces per ID. Its optional maximum witnesses are
analytically derived: 100,000 score calls, 50,000 bid calls and 1,000 ride calls.
Their domain sizes remain valid even if a particular existing runner cannot admit
their transport size. Freeze exact framed packet/output sizes before execution;
never raise caps or silently reduce the official domain to clear a test.

The largest legal score sum is below 100,000 times one billion, safely below
JavaScript's exact-integer bound. Bid and rider identifiers/results also stay in
their pinned integer ranges. Candidate complexity is stated in `contracts.json`;
it is source reasoning, not a measured runtime or memory result. No optional
follow-up has been converted into a mandatory gate.

Validation here is source-free reference/contract testing, Python AST parsing,
JavaScript syntax checking and fatal Ruff checks. No candidate has been executed,
independently qualified, canonically adopted, deployed or claimed accepted by the
official judge. The authoring catalogue retains unknown qualification status.

Source-free checks:

```sh
python3 test_oracles.py
python3 test_case_contracts.py
python3 test_native_observer.py
node test_native_observer.cjs
```

Do not import the numbered candidate modules into these host tests.
