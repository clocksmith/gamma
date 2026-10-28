# Separate Python 695 iterative-repair qualification preparation

This fixed controller references the existing authored repair owner
`../authored/repair-python695-iterative-20261028-v1`. It preserves the original
batch05 programs, controller, execution freeze and observations. It does not
register a competing source inventory, modify repair source, change sandbox
limits or qualify an official wrapper.

The source is fixed to SHA256
`b04cfc350cf30124e728f3ace84114a3311f55b729f3d1a6f85bdec19bb550ec`;
manifest `72cdfb51c1e7fb01416172071a55a73b4458b843e72346de72bc00573b9c8731`.
Only Python, problem695, exact `solve(grid)` semantics and the existing Python
value/effect observer are admitted. All opens require the existing live boundary
gates; source visibility and a static review confer no cached access authority.

The authored 72 independent cases are regenerated and crosschecked against the
existing independent DSU helper before freeze and replay. They cover every binary
2-by-3 grid, minimum land/water, maximum 50-by-50 land/water/checkerboard,
maximum row/column and the 1275-cell snake. Expected outputs remain on the host.
The exact mandatory review is supplied privately, not included in this directory:
`6d80496f7736256e99652818a59606391c693d75d6f5df4d3dc0c50ac571b673`.
`accept_manual_record` verifies all seven flags and exact source, contract,
reference, case-generator, official content/API and observer hashes. The API
hash uses sorted compact ASCII JSON with nonfinite values forbidden; source and
review records are never rewritten to fit an execution identity.

`protocol.py prepare --gate FILE --gate-sha256 SHA --statements NEWDIR` performs
one live-gated official695 public refetch, retaining its response before exact
original snapshot/content/API validation. Changed or unavailable definitions
block the lane. No premium/private fallback is provided.

`freeze` requires those gate/statements arguments plus `--review FILE`,
`--preflight LOG --preflight-sha256 SHA --freeze NEWFILE`. It requires the actual
existing Linux runtime and exact passing37-check judge preflight. It freezes
source/helpers/runtime, public snapshot, review, cases and the existing batch05
prospective host/output plan. It cannot create a runtime freeze on this Mac.

`run` requires gate/statements/review arguments, `--freeze FILE
--freeze-sha256 SHA --output NEWDIR`. Each dispatch repeats the live source gate,
exact source and observer checks. Original stdout/stderr and process metadata
are saved immutably before host verdict. Dispatch exceptions are retained without
fabricating a process result. Failed or partial runs cannot pass by omission.

`replay` uses the same inputs/output directory, regenerates references and checks
exact freeze/runtime/source/input identity, raw hashes/byte counts, process
status and saved report without calling the sandbox. Its immutable `replay.json`
records raw-stream hashes and original/relocated gate identities; relocated gate
paths may differ only with identical six trust anchors.

Resource limits remain the existing CPU3s, wall8s, memory1GiB, process16,
descriptor64, child-file-write1MiB and stdout16MiB limits. The prospective host
packet budget is16MiB; child RLIMIT_FSIZE is not a host-input cap. No provisioning,
private transfer, cap changes or actual candidate execution is part of this
source preparation. A successful future finite run does not revalidate the
original recursive variant or establish universal/generalization claims.

Source-free controls:

```sh
python3 -m unittest -q test_protocol
```
