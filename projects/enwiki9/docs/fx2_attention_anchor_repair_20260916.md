# Deliver the attention mode to its actual compiler

`fx2_attention_anchor250k_v1` completed 32 execution phases, but its treatment
was never enabled. The makefile compiles transformer objects with
`CPPFLAGS_TRANSFORMER`, independently of the two compressor flag variables.
Every actual attention compile command omitted `GAMMA_ANCHOR_MODE`; the header
defaulted to zero. All four executables, neural streams and archives matched
the parent. This is an implementation failure, not evidence against retention.
The immutable runner decision is qualified by the independent terminal failure
receipt and validated retry reflection.

`fx2_attention_anchor250k_v2` changes only build delivery and its verification:

- Keep every original transformer compiler flag and append the intended mode
  through `CPPFLAGS_TRANSFORMER` for K, D and S.
- Make an absent mode a compiler error in the child header.
- Read each actual compile log and require the correct mode on `model_opt.cpp`.
- Require D and S executables to differ from P before invoking either codec.
- Charge the complete additional make-variable assignment as an option
  component, alongside the measured source ZIP difference. Official option
  minimization and complete packaging remain unresolved.

The selected first-four and later-four states, 1024-slot capacity, original
rotations, weights, reset policy, exposed 250KB population, native 32 phases,
inverse/repeat checks, guards and decision inequalities remain unchanged.
The [original design](fx2_attention_anchor_20260916.md) supplies the mathematical
retention invariant and scientific question. No anchor-count or position
selection follows from the failed build.

Preflight repeats the independent queue test using the corrected header,
requires compilation without a mode to fail, proves the new log validator
rejects the old K/D/S build logs, and inspects prospective native make commands.
Those checks establish parameter delivery, not compression value. The corrected
corpus comparison must supply the missing archive evidence.
