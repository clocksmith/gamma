# Detection and repair diagnostics on eight authored task/mutant pairs

Track A step 4 of the combined Gamma plan. [pairs.json](pairs.json)
(`gamma.authored-mutant-diagnostics.v1`, owner-supplied 2026-11-12) holds eight
synthetic tasks, each with a correct and a mutant base-v2 graph and a
distinguishing example. All 16 graphs validate and each pair gives its stated
outputs on the distinguishing example in this repository's interpreter. The
file's `runtime_source_sha256` (`af87ad91…`) matches none of the local runtime
files (`typed_program.py` is `487ec034…`) and is recorded as unmatched.

[run_mutants.py](run_mutants.py) on Jupiter (host 128). Authored here:
- **Scoring domain:** every input of the task's stated domain (M02: all lists
  of 0–3 pairs with components in −2..2, a bounded sub-domain).
- **Weak public example:** the first domain input on which correct and mutant
  agree.
- **Synthetic logits:** uniform margins making each mutant decision the argmax.
  Repair order therefore shows reachability, not a model's ranking.

## Results ([report.json](report.json))

| Pair | Mutation | Mutant domain accuracy | Separating cells | Detection (weak example) | Repair (distinguishing example added) |
|---|---|---|---|---|---|
| M01 | integer literal | 0.5% | literal, 1 bit | wrong acceptance | **repaired**, correct on the full domain |
| M02 | Boolean literal | 4.8% | literal, 1 bit | wrong acceptance | not reached: pool bound (below) |
| M03 | operation substitution | 0.5% | operation (pure:sub → pure:add) | wrong acceptance | not covered: no pure-operation family |
| M04 | operand order | 0.5% | binding | wrong acceptance | not covered: no binding family |
| M05 | same-type reference | 0.5% | binding | wrong acceptance | not covered: no binding family |
| M06 | branch placement | 0.5% | binding, operation, structure | wrong acceptance | not covered: multi-class |
| M07 | loop-bound structure | 1.0% | operation, structure | wrong acceptance | not covered: multi-class |
| M08 | effect order | 0.5% | binding | wrong acceptance | not covered: no binding family |

- **Detection:** under the weak public example every mutant is accepted (8
  wrong acceptances). That is weak evidence, not a route defect: the route
  accepts example-consistent candidates by policy.
- **Repair:** with the distinguishing example in a separately frozen request,
  the existing recipe-then-bit-flip repair reaches 1 of 8 (M01). No wrong
  acceptance in the repair setting.
- **M02 (observed):** the needed Boolean flip is one bit away, but the integer
  field-index literal earlier in the graph has 129 equally scored bits, which
  fill the 8-entry pool before the Boolean's single bit. 36 attempts ran, most
  rejected as invalid field indices. This is a property of uniform margins plus
  the pool bound; a model's margins would order it differently.

## Next interventions indicated (one family at a time, guarded semantic route as control)

- Pure-operation substitution: M03 (and part of M06, M07).
- Same-type binding rewiring and operand order: M04, M05, M08.
- M06 and M07 combine structure with operation and binding changes; they are
  not local repairs and are candidates for partial-program construction rather
  than bounded repair.

Engineering diagnostics on authored fixtures only, with synthetic logits; not
model, training or generalization evidence.
