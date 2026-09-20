# Matched native-forward training and counted core delivery

The fixed training comparison is closed. J reduces the measured sample-plus-model
cost, but worsens the payload on both populations. **This profile does not advance
to 10 MB or 100 MB.** Preserve trimmed P as the scale comparator and keep A/J as
measured checkpoints. No metadata, extra optimizer updates, or unrelated codec
was introduced. The objective remains **96,000,000 complete bytes**, with
95,000,000 stretch; Gamma's verified full-corpus score remains **unknown**.

## Training result

[The closed receipt](../results/fx2_matched_train250k_q0_v1/terminal.json)
and [comparison](../results/fx2_matched_train250k_q0_v1/comparison.json) bind
fresh native-forward training from preserved P. Each arm receives 16 AdamW
updates at learning rate 0.00002, seed 923, four matched actual native piece
starts, 512 causal warmup rows and 128 loss tokens per window. That is 2,048
loss-token exposures per arm, not full-corpus training. The starts are
0, 2611, 39712, 68859 in the retained opening capture. A optimizes data only;
J adds the previously declared two-copy weight-histogram surrogate.

Every update exports current tensors into native inference. The backward remains
a whole-reference surrogate Jacobian. Packed checkpoint inference also agrees
exactly with raw-export inference on the declared export check. Both arms change
parameters; these are trained checkpoints, not configurable predictor shells.

| Checkpoint | Native loss on 512 training-window truths, bits | Packed weights |250 KB archive |1 MB archive |
|---|---:|---:|---:|---:|
| P |1,100.611418 |2,930,652 |33,429 |131,238 |
| A: data only |131.407373 |2,929,755 |40,538 |Not selected |
| J: joint cost |128.726667 |2,905,937 |39,717 |154,921 |

These losses are reevaluated after training on the same 512 distinct truth
positions, separate from the 2,048 repeated optimizer exposures. Relative to P,
reference/native loss differences are -966.520/-969.204 bits for A and
-968.214/-971.885 bits for J. Numerical evaluation therefore preserves the
training-window improvement; it does not establish useful off-window prediction
or final-mixer behavior.

The frozen development ranking uses actual archive plus two packed-model copies.
A loses 5,315 component bytes; J saves 43,142. J's identities were recorded in
[selection.json](../results/fx2_matched_train250k_q0_v1/selection.json) before
confirmation opened. Confirmation is raw[713000000,714000000), outside this
training population but previously exposed in other research.

On confirmation, J saves 49,430 model bytes across two copies and loses 23,683
payload bytes, leaving **25,747 component bytes saved**. Both finite comparisons
include the whole model cost once per required copy; no small-sample gain is
multiplied into a corpus forecast. Actual source/executable accounting is a
separate delivery measurement below.

All five measured archive arms passed independent exact inverses and deterministic
repeats. The guard closed without violations: peak cgroup memory 6,361,174,016
bytes; peak allocated scratch 378,400,768 bytes. Timing is shared-host diagnostic.
The recipe's original manifest omitted an explicit codec reference, although its
experiment closure binds the precise native source, model and inputs. Original
bytes remain intact. New seal/admission checks reject that incomplete declaration;
the delivery descendants explicitly declare codec and model identity.

The regression does not isolate limited population coverage, surrogate-gradient
quality, or final-mixer adaptation as its cause. It stops this fixed profile,
not the entire idea of jointly training data and model description cost.

## Complete bounded delivery

[Trimmed P's delivery receipt](../results/fx2_core_delivery250k_q0_v2/terminal.json)
now proves a functioning bounded core package. `make` builds `comp9`; running
`comp9 INPUT` creates `archive9`; `archive9` takes no arguments and writes the
original bytes to `enwik9`. Outputs are never overwritten. The envelope carries
the exact native binary, raw dictionary and packed model; it changes no predictor
or frontend computation on this tested core path.

Independent clean builds reproduce the compressor. Restricted execution exposes
only the delivered archive, five pinned ELF runtime providers, and kernel
`/proc`/`/dev`; it mounts no repository, original corpus, Python, or observer
package for decoding. Whole archives repeat exactly and the embedded payload
matches the retained native archive.

P's 250 KB fixture costs **7,642,117 bytes** as executable compressor plus archive,
or **7,780,846 bytes** as source ZIP plus archive. These are alternatives. Each
executable contains 22,832 envelope bytes, 438,792 codec bytes, 411,996 raw dictionary
bytes, 2,930,652 model bytes, and a 72-byte footer. The decoder additionally carries
the 33,429-byte payload. Thus the old 45,056-byte trim measurement is retained as
a component observation, without ignoring the new envelope and asset costs.

[The selected J delivery](../results/fx2_joint_delivery250k_q0_v1/terminal.json)
passes the same checks, including a fresh P control encode/decode. Its complete
P control files match the independent parent package byte for byte.

|250 KB fixture delivery | P | J | J saving |
|---|---:|---:|---:|
| Executable compressor plus self-extracting archive |7,642,117 |7,598,975 |43,142 |
| Source ZIP plus self-extracting archive |7,780,846 |7,737,699 |43,147 |

No extra invocation options are required; the actual compile recipe and native
arguments are inside the counted source/executable. These are complete **fixture**
totals, never substitutes for the full 1 GB score. J's native payload remains
39,717 bytes. The selected package guard closes without violations at a peak
cgroup memory of 5,910,818,816 bytes.

Retained deliverables:

- [J source package](../results/fx2_joint_delivery250k_q0_v1/comp9.zip)
- [J executable compressor](../results/fx2_joint_delivery250k_q0_v1/comp9)
- [J self-extracting 250 KB archive](../results/fx2_joint_delivery250k_q0_v1/encode/archive9)
- [J trained checkpoint](../results/fx2_matched_train250k_q0_v1/training/J/checkpoint.tch)
  and [packed native model](../results/fx2_matched_train250k_q0_v1/training/J/weights.tfwc2)
- [P source package](../results/fx2_core_delivery250k_q0_v2/comp9.zip)
  and [P self-extracting 250 KB archive](../results/fx2_core_delivery250k_q0_v2/encode/archive9)

The pure architecture group passes 144 tests and 54 subtests. The native group
passes 6 tests, including the new envelope execution fixture. Two focused training
window/target tests pass, and changed Python modules compile/import successfully.
The envelope fixture checks inverse, malformed footer rejection and refusal to
replace an existing output. New admission tests reject a recipe missing its
codec identity before either sealing or tool admission.

This is a complete **bounded core-profile package**. It does not exercise the
upstream full-enwik9 split/reorder submission frontend or establish a full 1 GB
score. The initial package attempt stopped before building because `bwrap` had
changed since the historical runtime profile; that failed closure and reflection
are preserved. Its successor binds current tooling without rewriting old hashes.

## Qualification and next action

The [qualification readiness record](../operations/provenance/fx2_qualification_readiness_20260920.json)
keeps the remaining conditions explicit. Existing Geekbench assets match their
recorded identities, but the historical plan binds older Python and lease code.
Calibration requires a fresh prospective binding and isolated admission. Foreign
workloads were present during these diagnostic runs; no calibration allowance
has been inferred from their timing.

The package includes original GPL/source notices, Gamma's MIT text, and retained
LLVM/CUDA notices. That does not resolve model permissions or CUDA-derived math
licensing. The [committee inquiry](hutter_committee_inquiry_20260919.md) is prepared
but unsent because no email sender is connected.

Do not increase this optimizer budget, introduce metadata, or scale J based on its
fixed model saving. Preserve both delivery alternatives and the strong parent.
Any next scientific mutation needs a distinct hypothesis and paying native archive
evidence. Full submission still requires exact full-corpus delivery, applicable
accounting, source/license eligibility, calibrated resources and committee review.
