# Tinker to Doppler Browser Adapter Evaluation

This SAME-R domain evaluates whether a PEFT adapter trained by Thinking
Machines Tinker survives export and browser deployment without losing its task
gain or base capability. Gamma selects candidates. Doppler owns artifact
identity, adapter import, F16 parity, quantized-browser parity, and execution.
Reploid owns Shadow staging and human-authorized promotion.

## Frozen boundary

One evaluation input binds:

- the base checkpoint and adapter byte identities;
- disjoint sealed task and retention populations;
- passing Doppler identity and parity receipts;
- base and candidate scores under one task metric;
- a retention regression limit; and
- four separate determinism levels.

The four levels are not interchangeable:

| Level | Question |
|---|---|
| Same-device run-to-run | Does the same workload repeat on the same device? |
| Same-device batch invariance | Does batching change the result on one device? |
| Cross-device numerical | Do devices stay inside a declared numerical tolerance? |
| Cross-device output agreement | Do devices emit the same selected outputs? |

Each level declares whether it blocks selection. A tolerance result cannot be
reported as bit equality. Output agreement cannot be reported as numerical
equivalence.

## Run the evaluator

```bash
python projects/samer/domains/tinker_browser/evaluate.py \
  --input projects/samer/domains/tinker_browser/fixtures/synthetic-pass.json
```

The checked-in fixture proves evaluator mechanics only. Its IDs and hashes are
synthetic, and its claim boundary forbids treating the output as Tinker,
Doppler, Gamma, or Reploid capability evidence.

## Selection and promotion

Gamma returns `gamma_selected` only when the task gain, retention floor,
Doppler evidence, and every required determinism level pass. Its receipt always
sets `promotionAllowed: false`. Reploid must independently verify the exact
receipt and obtain human authorization before activating a trained adapter.

Owner contracts:

- input schema: `evaluation-input.schema.json`;
- evaluator: `evaluate.py`;
- Doppler profile: `tinker_peft_browser_adapter` in the trainer artifact bridge;
- outer method: `projects/samer/README.md`.
