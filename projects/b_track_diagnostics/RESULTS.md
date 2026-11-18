# Development stop-channel intervention

Exploratory, not confirmation. Seed 23017; 24 authored tasks, 12 specialties.
The same semantic phrase pools recur across formatting conditions, so these are
not 24 independent statistical replicates. No significance claim is made.

| Regime | Identity correct | No-stop correct | Identity empty | No-stop empty | No-stop truncated |
|---|---:|---:|---:|---:|---:|
| Prompt removed | 12/24 | 0/24 | 12/24 | 0/24 | 18/24 |
| Prompt present | 11/24 | 19/24 | 7/24 | 0/24 | 0/24 |

Paired changes: prompt-present 9 wins / 1 loss; prompt-removed 0 wins / 12 losses.
Mean decode time: prompt-present 587.81 -> 632.69 ms; prompt-removed
154.10 -> 325.91 ms. These are descriptive, single-run timing observations,
not a speed benchmark. Setup cost is not included in these decode means.

The intervention removes only the compiled stop B row. It reduces blanks but
can destroy termination without context. It is not a general fix.
The decoded first-token-newline flag is false even for blank outputs with raw
token [198]; use raw tokens/empty-output counts, not that flag for attribution.

All 96 unique arm/regime rows were saved with completed=true. The Node process
then lingered and was terminated by the 600-second watchdog. Evaluation data
are complete; clean shutdown is not verified. No frozen protocol or receipt
was modified, and the authored phrase pool is independent of v4 confirmation.

development_receipt.json retains all rows and executed-source hashes; its
resource-availability note was omitted for publication. Portable path resolution
was added to the runner after execution, so its current digest differs from the
recorded executed digest. The intervention and task-source hashes remain exact.
