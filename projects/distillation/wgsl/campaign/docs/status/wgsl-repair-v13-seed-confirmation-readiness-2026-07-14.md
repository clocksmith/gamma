# WGSL Repair V13 Seed-Confirmation Readiness

The authoritative V13 seed-confirmation population is materialized and has
passed reference qualification. Seed 29 has not received any confirmation
prompt.

The population derives from freeze commit
`327589ac633f15dc9ace2d13a48ab1512edef2c8` under the stratified V2
materializer. Its manifest SHA-256 is
`e86d55497329d5d6adfd579b726b980bf7d42386f1df74d740ff0903fdefb3e9`.
It contains eight disjoint tasks: four unary, four binary, four parameterized,
and four non-parameterized. The selected families are maximum, mean, scaled
square, negation, absolute pair distance, scaled difference, scalar addition,
and threshold masking.

The seed-confirmation evaluation policy SHA-256 is
`baabc1bfbc9c1e522a842403b5e89fc202bbd0fb5a6bddffef7caeca88ca5459`.
It admits only the already-selected external20 seed 29 adapter, preserves the
same exact F16 Qwen artifact and deterministic 64-token generation contract,
and permits one submission. Passing requires 8/8 semantic tasks, 8/8 compiler
passes, 24/24 primary semantic variants, 8/8 response-contract passes, and 8/8
historical-regression passes.

The readiness receipt is
`wgsl-repair-v13-semantic-readiness-pre-confirmation-2026-07-14.json` with
file SHA-256
`c165d43094fce6042f28df59a393ee0de08f5a6ad417bb4751e056fbbb8197ec`.
It sets `seedConfirmationAllowed: true`. Promotion evaluation, semantic
promotion claims, WGSL Doctor, and complete shader writing remain false.

The unstratified V1 population remains invalid with no reference or candidate
execution.

The frozen reference shaders passed 8/8 compilation checks, 24/24 primary
dispatch variants, every CPU oracle, bounds check, metamorphic relation, and
historical regression on AMD RDNA3 Chromium WebGPU. The reference receipt is
`wgsl-repair-v13-seed-confirmation-reference-2026-07-14.json`, with file
SHA-256
`26b826be2d194c521d95680d675a6c4bbaf62e13a5d2cd320248a38a89885b32`.
After this receipt is pushed, the next admissible action is the policy's one
deterministic seed-29 submission.
