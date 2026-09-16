# Trimmed FX2: repair the auxiliary packaging path

The trimmed executable's native transformer path passed the reserved 1MB
comparison and is undergoing its unchanged 10MB comparison. Its original
self-extracting packaging path is nevertheless incompatible with that trim.
The source calls an auxiliary decoder without transformer weights, while the
trimmed predictor rejects the removed LSTM fallback. The measured 45,056-byte
executable reduction is consequently a **component measurement**, not a proven
reduction in a functioning self-extracting submission.

## The exact mismatch

The source ZIP `results/fx2_expert_release250k_v3/P-source.zip` is fixed at
3,905,220 bytes and SHA-256
`c44d941f95bd8504d63ed6ea5112af3ce15aeffb6874ebddb66596ce083c3cf6`.
Its predictor requires the native transformer profile on the ordinary mixer
path. The original self-extractor still makes these calls:

```
./cmix -d .new_article_order.comp .new_article_order
./cmix -d .dict.comp .dict
./archive9 -d .dict.comp_decomp .dict
```

Those calls have neither transformer weights nor `--ppmd-only`. The upstream
build script similarly encodes the auxiliary dictionary/order through the
ordinary auxiliary model. Passing transformer weights to the main corpus
codec does not repair this separate bootstrap path.

The existing PPM-only predictor returns before construction of the removed
fallback. Its decoder implementation already accepts a PPM-only predictor,
but the command-line policy rejects `-d --ppmd-only`. This separates two concrete
repairs from any change to the main predictor.

## Separate realization

`fx2_trim_auxiliary_ppm_v1` materializes a **new source package**:

1. Permit precisely PPM-only decoding, retaining the other option restrictions.
2. Add `--ppmd-only` to the three auxiliary self-extractor calls.
3. Add a source-delivered packager that verifies the fixed dictionary, order,
   and model; independently encodes/decodes both auxiliary assets; and assembles
   the original four-integer footer with every component included.

The packager requires a separately built native binary and a fresh directory.
It does not download assets, change the dictionary/order/model, invoke a teacher,
or remove bytes from accounting. It is implementation for a future admitted
native comparison, not permission to execute one outside the lab.

The materializer rejects changed source preimages. The new package changes only
`src/runner.cpp` and `src/readalike_prepr/self_extract.h`, adding
`gamma_pack_auxiliary.py`. Predictor, arithmetic coder, model and dictionary
members remain byte-identical. That source observation does not establish
compiled main-probability parity on a changed binary.

## Established checks and costs

[The preflight](../operations/provenance/fx2_trim_auxiliary_preflight_20260916.json)
records six passing tests. Two C++ probes compile the actual option parser,
validation policy, and footer layout extracted from the bound sources. They
verify the new decode request, nine rejected combinations, twelve unchanged
policies, and a 16-byte native header. Their file-readability check is stubbed;
they do not establish runtime file availability. Other tests check the exact
source difference, changed-preimage rejection, and synthetic package assembly.

The original source ZIP is reproduced byte for byte. Two independent child
materializations produce the same ZIP. The child is **3,907,353 bytes**, an
increase of **2,133 bytes** over the trimmed source ZIP. It is 3,215 bytes below
the original 3,910,568-byte source ZIP, before any other packaging differences.
These are alternate source-component comparisons, not full scores or an amount
to add to the native executable saving. The changed native executable size and
the new auxiliary compressed sizes are unmeasured.

The earlier prefix-dictionary experiment changed the dictionary representation
and retained the public online-LSTM auxiliary backend. Its negative result
remains intact. This realization preserves both asset byte sequences and changes
their auxiliary backend specifically to repair the removed dependency. It
inherits no prefix-dictionary gain.

## Required native comparison

One separately frozen native gate must compare original and repaired source
builds, repeat clean builds, encode/decode/repeat each fixed auxiliary asset,
and measure the actual package difference. It must exercise the real embedded
asset extraction calls in a restricted environment, then replay the unchanged
main transformer path on the exposed opening sample with exact reconstruction
and repeats. A tested bootstrap fixture may expose the source extraction
functions directly; it must be identified as a test fixture, not the released
binary or a full-corpus self-extraction result.

The component improvement is the old complete set of required components minus
the new set under the same packaging arrangement. Savings in the executable
can be outweighed by larger auxiliary streams or added build material. No
probability improvement, full-corpus result, license closure, target-platform
qualification, or winning score is claimed here.

The active trimming gate and held value-feedback gate are unchanged. The
value-feedback experiment retains its current next-execution priority. This
packaging repair does not reopen the retired linear correction families.
