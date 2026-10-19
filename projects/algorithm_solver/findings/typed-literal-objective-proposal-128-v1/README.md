# Literal objective experiment proposed, not authorized

The remaining consumed-fit errors are lcd:1101 (three literal bits) and lcd:1489
(seven). The qualified graph exists in both cases; after structural correction,
all supervised nonliteral fields match a qualified target. Public fallback binding
fixed one sentinel but produced no solving gain; its remaining correct bit pair
ranked tenth, outside the frozen four-execution budget. Stop additional repair
variants on these same outcomes. The original failed attempts remain evidence.

The existing literal head averages binary cross-entropy across 129 bits for each
supervised literal. Only 74 of 15,093 fit labels are set. An all-zero predictor
therefore achieves 99.51% bit accuracy. This is a testable objective mismatch,
not proof that balancing will improve executable programs. Low absolute logit
margin is also not a semantic error detector; the repair ranking cannot recover
more edits than the frozen proposal permits.

Propose **typed-literal-balanced-pair-128-v1**, a matched pair of new 400-step
runs, one existing-loss control and one class-balanced literal loss. Both use
seed 17 and identical freshly initialized predictor parameters, width 64, two
layers, AdamW lr 0.001, full fit batch, four retrieved fit graphs, the existing
43-label/129-bit codec and the fixed final checkpoint. No vocabulary expansion,
new model, download, checkpoint sweep, early stopping or target-guided repair.

For each example the candidate literal loss is the mean of the mean positive-bit
BCE and mean negative-bit BCE, over classes actually present. Ignore -100 exactly;
an example with no supervised bits contributes zero. Other heads and the minimum
loss over qualified graph alternatives are unchanged. At zero logits both
objectives give log(2), avoiding an arbitrary initial literal-head scale change.
Compare per-head loss, complete literal-value accuracy and executable correctness;
do not select a checkpoint using aggregate bit accuracy or independent tests.

Use the recovered original 15 fit graphs / ten fit problems and exact frozen
Qwen encoder. The completed [tokenizer-only preflight](preflight.json) found two
original fit-memory strings of 1,565 / 1,660 tokens; lossless compact JSON still needs
1,125 / 1,189 tokens. Neither representation fits 1,024. Preserve this failed shortcut.

The exact revised proposal uses **2048 tokens, truncation disabled**, for both
training arms, retaining the original digest-plus-JSON text byte-for-byte. All
25 fit/query inputs fit this limit (maximum 1,660); model config permits 32,768.
This is a new full-context matched experiment, not historical reproduction.
Use a local run-specific encoding function; do not change global MAX_TOKENS,
serving behavior, the model/tokenizer, or the frozen codec. Assert full token lengths
before allocating the encoder. If inputs or hashes drift, stop. Keep all fit graphs.

The encoder is frozen. Use CPU float32 for both training arms; the current GPU
reuse evaluation is separate and cannot silently authorize a precision change in
this training experiment. Encode in batches of one and release encoder memory before predictor optimization.
Sequential arms, at most four CPU threads, 8 GiB process tree RSS, 5 GiB total assets
and run disk, 900 seconds per training phase and 2,400 seconds overall. Preserve
partial failure artifacts; never silently retry. No training is currently running.

After both final checkpoints are sealed, compare raw, the already frozen guard
repair, and nearest fit graph on the same ten consumed fit inputs. Seal **all**
public decisions for both candidates before original hash-bound independent tests
are opened. Count end-to-end embedding/retrieval/prediction/assembly/public checks;
setup and independent scoring separately. Use the same hardware/dtype in both
arms and preserve CPU latency failure rather than attributing it to the loss.
A useful fit result requires at least one more independently correct raw answer
and one more independently correct guarded answer than matched unbalanced control,
zero wrong acceptances, zero lost correct answers, and no infrastructure failure.
The unchanged two-second p95 gate remains a separate requirement. Even a pass is
consumed-fit development evidence, not 2a completion or 2b generalization.

The eight original audit requests, protected 66 targets / 60 families and nearby
variants remain unopened by this proposal. Audit progression needs a separately
frozen candidate and authority; new training never grants protected access.

**Required owner approval:** authorize exactly this paired 2x400-step experiment,
including the shared 2,048-token full-text context, within the stated budgets. This does not authorize the older
rebuilt-corpus training proposal, installs, new models or expanded search bounds.

The [complete owner approval packet](OWNER_APPROVAL.md) and
[machine-readable identities and bounds](owner-approval-packet.json) now include
the original/checkpoint/initialization hashes, explicit family separation, full
combined budget, matched baseline and GPU measurement caveats. The opt-in loss
implementation passes eight tests plus two subtests; no optimizer step occurred.
