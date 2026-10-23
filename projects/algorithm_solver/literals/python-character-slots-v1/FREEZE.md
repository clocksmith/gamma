# Item34 prelaunch freeze: Python character slots v1

**Frozen for Claude review after root design/resource review; launch remains pending approval and core release.**
[Design](DESIGN.md) is the full method and gate specification.

Immutable parents: item31 recorded84a4c7310; actual-flow solver item24. Pin only
allowed existing private artifacts by opaque hash. All31 source and dictionary
files remain unchanged. No protected or closed14 Python IDs, no new source
qualification, no all50 loader. Four arms:128fixed96/optional and256fixed96/optional.
Use own-width31scope_joint seed and R baseline. No cross-width selection.

Freeze code, decoder, runtime, public passing receipt and private-input hashes in
[contract.json](contract.json). Four single-core workers4/5/6/7, threads1,
8 repairs/60 solver seconds/600 whole-phase seconds per arm,1200 whole execution
seconds and30 supervisor cleanup seconds. Queue after30 releases those cores.
An8GiB address-space cap applies per parent/worker before fit input loading.
Optimized Python and PYTHONOPTIMIZE are forbidden. Root must review this resource queue and Claude must review this freeze before
launch. Search failure or timeout leaves durable failure metadata and partial
artifacts, invalidates promotion and cannot be restarted under the same identity.

During execution, all four fit seals precede any validation source reads/hashes.
The only exception is prelaunch contract preparation: opaque hashes of existing
authorized input files may be computed without parsing source contents. Use strict
source-hash reuse of passing31 qualification. Python method/body/full-source
bans, actual-entry-only coverage, reserved fit-unseen characters. Strict exact
fit-N acceptance only. Record feasible/infeasible solver outcomes and all rejects.

Readiness versus R: at least5% fewer validation actions, strict median/p90,
>=6 improve and<=2 worsen among9, nonincreased C fraction,<=105% package, complete
coverage/qualification and clean entry audit. Incrementals versus BOTH31seed and
matchedfixed96: strict actions, nonincreased median/p90/C,<=2 worse,<=105% package.
Report both width verdicts independently, no posthoc width choice. M1 unchanged.

Prepare metadata with the pinned SciPy interpreter's `make_contract.py`; execute
`launch.py --output <new-private-path>` only after review. Rebuild separately with
`report.py --run <private-path>`. Reporting refuses failed/partial execution and
independently verifies source/qualification, seals, canonical packet IDs and costs.
Failed execution or replay writes a durable incomplete reporting receipt with no
verdict. Numbered predictions P1–P4 in DESIGN are evaluated separately from gates.
Synthetic tests do not establish corpus performance or numerical qualification.
