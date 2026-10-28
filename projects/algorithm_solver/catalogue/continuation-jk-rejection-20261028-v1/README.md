# J/K judge rejection measurement

Evidence class: rejection accuracy of the fixed J/K judge on seeded wrong variants. This is judge evidence, not candidate qualification. It changes no admission, adoption or qualification status, and makes no claim about defects outside the operators below.

## Question

The [J/K qualification lane](../continuation-jk-qualification-20261028-v1/README.md) shows which originals pass its frozen finite cases. Passing alone does not show that the same cases, observers and verdicts reject wrong programs. This lane measures that directly. Every variant of a passing original receives the exact frozen J/K cases, batch plans, observers, sandbox limits, access gate and verdict function. Only the program bytes change.

## Variants

A variant is the byte-preserved original source followed by one fixed wrapper from [variants.py](variants.py). The wrapper replaces the exported `solve`. In Python, recursive and helper calls still reach the original while it runs, so the wrapper adds no frames below the outer call.

| Operator | Defect class | Changes the outcome when | Confirming verdicts |
|---|---|---|---|
| `control-copy` | none (control) | never; deep-copies arguments and result | must pass every batch |
| `wrong-always` | value | every call | `result_value` |
| `wrong-on-degenerate` | value | every list/string argument has length ≤1 | `result_value` |
| `wrong-on-large` | value | some list/string argument has length ≥1000 | `result_value` |
| `wrong-on-duplicates` | value | a list of safe integers or of strings repeats a value | `result_value` |
| `wrong-on-negative` | value | a top-level or first-level safe integer is negative | `result_value` |
| `wrong-on-zero` | value | a top-level or first-level safe integer is zero | `result_value` |
| `wrong-on-repeat-call` | hidden state | second and later calls in one process | `result_value` |
| `wrong-type` | interface | every call; same value, different result type | `result_type`, `candidate_error` |
| `input-mutation` | effects | a list argument exists; appends after computing | `input_effects` |
| `alias-equal-input` | aliasing | the result, or one of its list elements, equals an input list; returns the input object | `return_aliases` |
| `slow-on-large` | resource | as `wrong-on-large`; spins 12 s before computing | `sandbox_process_failure` |
| `memory-on-large` | resource | as `wrong-on-large`; allocates beyond the memory limits | `sandbox_process_failure`, `candidate_error` |

Value perturbations keep the result type: booleans flip, numbers add one, strings gain a character, and lists drop their last element (an empty list becomes `[0]`). Every J/K problem uses the exact return policy, so any changed value is wrong.

## Host-predicted triggers

The host mirrors each wrapper decision per language from the wire arguments and expected results. It uses UTF-16 string lengths for JavaScript and treats integral numbers as JavaScript does. Wire bigint and node encodings are ignored on both sides. The plan therefore knows, before execution, which cases each variant must fail. [test_variants.py](test_variants.py) runs the real observers on toy programs, never on J/K candidates, and checks that every operator changes the outcome exactly where the host predicts.

## Procedure

Run this only on the Linux executor, after the J/K `run` and `replay` have both completed:

```
rejection.py run --gate GATE --gate-sha256 HASH --statements DIR --freeze FREEZE --freeze-sha256 HASH --baseline JK_RUN_OUTPUT --output NEW_DIRECTORY
rejection.py replay (same arguments)
```

The run proceeds in five steps:
1. `run` re-verifies the J/K freeze, the runtime, the gate, the sources, the statements and the cases.
2. It requires a J/K report and host replay bound to that freeze. Only originals whose admitted cases all passed receive variants; the rest are recorded as `original_not_passing`.
3. Each seeded variant runs only the batches that contain a triggering case, in plan order, and stops at its first failing batch. The control runs every batch.
4. Variants with no triggering case are recorded as `not_triggered`. That status records the case set's coverage of the trigger; it is not a judge error.
5. Raw streams and process metadata are saved before verdicts, as in J/K. `replay` rebuilds the plan, every verdict and the report from the saved streams without executing anything.

## Outcomes

| Status | Meaning |
|---|---|
| `rejected_confirming` | Rejected with the intended verdict on a triggering case |
| `rejected_other` | Rejected, but not by that verdict on a triggering case; inspect the failures |
| `false_acceptance` | Every triggering batch passed: the judge accepted a wrong program |
| `control_accepted` / `control_rejected` | The behavior-preserving control passed every batch, or did not |
| `not_triggered` | No frozen case exercises the trigger |
| `original_not_passing` | No variants; the original did not pass |

Rejection accuracy for an operator is `rejected_confirming / (planned - not_triggered)` over eligible originals, reported per language. The false-rejection rate is `control_rejected / controls`. A `control_rejected` caused only by the copy's extra time or memory on maximum cases is a resource cost of the control, and is reported as such.
