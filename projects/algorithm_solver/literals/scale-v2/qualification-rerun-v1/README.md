# Qualification rerun v1

Fresh execution of the stored [scale-v2 qualification](../qualification/report.json)
on 2026-10-21, before its 80-problem inventory (80 original, 80 canonical and 80
compact sources in [the manifest](../generated/manifest.json)) is used in matched
comparisons. The stored receipt had been joined into later work, not rerun.

The rerun reproduced **240/240 source versions**, **25,236/25,236 checks** and
**8,412 distinct cases**, with identical generated-manifest, checks and harness
hashes. All 510 raw observation files were byte-identical to
`../qualification/observations/`, and regenerating the rewritten sources from the
originals reproduced all 240 manifest hashes. The only differences are per-call
wall-clock `seconds` across 255 sandbox calls; elapsed time was 17.94 s against
17.84 s recorded.

It ran on 128 at commit `9c3e5d2bf` from a fresh git archive under `/tmp` (deleted
afterwards), with the Python 3.13.15 recorded in
[clusters-v1/REPRODUCE.md](../../clusters-v1/REPRODUCE.md), node v22.22.1 and the
existing bwrap sandbox. Judge and lane acceptance passed (37/37) first. Exact
commands, environment and both report hashes are in [comparison.json](comparison.json);
[report.json](report.json) is the receipt as written by `verify.py`.

This is the same evidence class as the stored receipt: finite development oracle
checks plus exact original output and input-effect parity. It is not formal
equivalence, official judge acceptance, maximum-size execution, human assembly,
autonomous solving or a vocabulary-design result.
