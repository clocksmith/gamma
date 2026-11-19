# CATSCAN: Prompt-to-adapter compilation study (B1 v5)

Parent: [Request-specific reconfiguration experiments](../CATSCAN.md)

## Target

Compile a table of examples into one small low-rank update on a frozen model, in closed form and
without gradient steps, so that the model answers new questions with the table removed as
accurately as the unmodified model answers them with the table in its prompt, at lower cost per
question.

## Authority

- Owns `projects/reconfiguration/query_swiglu_fastweight_v5/` (compiler, runner, task generator,
  tallies, protocol draft) and the receipts in `.work/query-swiglu-fastweight-v5/`.
- Reads the sealed v4 engine helpers. It never edits a v4 file or receipt.

## Scope

- A single-layer MLP `down_proj` update whose layer and ridge strength are chosen per table by
  leave-one-out accuracy on that table.
- Two disjoint task splits. Development uses the eight `dev` item groups only; the 37 `confirm` groups
  are reserved for a locked confirmation and the runner refuses them without a protocol hash.
  Confirmation tables follow a block design in which any two tables share at most one group.
- Models whose MLP output is added straight to the residual stream. Models that renormalise it
  (post-feedforward norm) are out of scope.

## Contracts

- Input: locally provisioned Q4K models, a clean Doppler checkout, the task generator.
- Output: receipts recording per-question outputs for every arm, per-table compile diagnostics,
  and the hashes of the runner, compiler, task file and model manifest.

## Invariants

- The base model's weights are never changed; removing the adapter restores it.
- The compiler sees the support table only. Query text and query answers never reach it, except
  the final token of the query format, which marks where an answer begins.
- Every comparison includes the base model with the table present and a guess-a-valid-code rate.
- The controls see what the compiler sees and no more: the most-frequent-code control reads the support
  lines; the classifier control reads the same anchor activations and support labels as the adapter.
- Development tasks never change: `design_check_v5.py` pins their hashes.
- One WebGPU process at a time, started only after the GPU is confirmed free.

## Acceptance

- `tally_v5.py` reproduces every reported count from a receipt.
- No result is called confirmed until a protocol is locked before the confirmation tasks are
  generated, and the confirmation is run once.

## Non-goals

- Beating a cached copy of the prompt on accuracy. A cached prompt gives the base model's
  with-table accuracy by construction; the adapter's case against it is size and freed context.
- Downloading model weights that are not provisioned.

## Freedom

- Adding arms, ablations and models during development, each as its own receipt.
