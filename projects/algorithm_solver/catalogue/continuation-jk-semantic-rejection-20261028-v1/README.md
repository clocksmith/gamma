# Targeted wrong programs for the J/K review gaps

Evidence class: the judge's outcome on realistic wrong programs aimed at the case-set gaps that the J/K reviews named. This is judge and case-set evidence, not candidate qualification. It changes no catalogue status.

[variants.json](variants.json) lists eleven variants. Each is an exact frozen original with one local defect, and [test_semantic.py](test_semantic.py) checks the bytes and the size of each edit:

| Problem | Language | Variant | Defect |
|---|---|---|---|
| 3820 | Python, JavaScript | `recursive-distances` | Depth-first recursion instead of breadth-first; deep trees exhaust the stack |
| 3820 | JavaScript | `int32-squares` | 32-bit `Math.imul` squares miss triples with legs above 46340 |
| 3821 | JavaScript | `float32-binomials` | `Float32Array` binomial rows round coefficients above 2^24 |
| 3825 | Python, JavaScript | `bits-0-28` | Bit 29 is never scanned |
| 3835 | Python, JavaScript | `single-shrink` | The window shrinks at most once per step |
| 3835 | JavaScript | `int32-cost` | 32-bit window cost wraps above 2^31 |
| 3850 | Python, JavaScript | `exponent-bound-prune` | States whose exponents exceed the element count are pruned, though a 4 adds two |

[semantic.py](semantic.py) runs every variant on the Linux executor through one unchanged freeze. With `--lane jk` that is the [J/K lane](../continuation-jk-qualification-20261028-v1/README.md), which has the original cases. With `--lane boundary` it is the [boundary lane](../continuation-jk-boundary-20261028-v1/README.md), which has the original plus the repaired cases.

The run proceeds in three steps:
1. Batches run in plan order until the first failing batch. If every batch passes, the variant is a false acceptance.
2. Raw streams are saved before verdicts.
3. `replay` rebuilds every verdict on the host without executing anything.

```
semantic.py run --lane jk|boundary --gate G --gate-sha256 H --statements DIR --freeze FREEZE --freeze-sha256 H --output NEW_DIRECTORY
semantic.py replay (same arguments)
```

Expected shape, from host simulations of each defect using independent reimplementations rather than the variant files: the original cases accept every variant except `single-shrink`, which they already reject. The boundary cases reject all of them. Results are in [RESULTS.md](RESULTS.md) once runs complete.
