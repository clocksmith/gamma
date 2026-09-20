# Review of the supplied CRG bundles

Read all seven supplied files and the import note at `679b0a721`. Verified their
bytes against that Git commit. The imports remain unchanged. This review adds
synthetic acceptance checks; it does not admit a corpus experiment or replace
Gamma's parked FX2 relational realization.

## What the files implement

| File within `external/crg-import-20260920/` | Responsibility |
| --- | --- |
| `optimized/README.md` | Format, claimed external tests, local non-enwik9 measurements and stated limits |
| `optimized/crg_reference.py` | Pure Python binary arithmetic coder, order-2/order-6 context parents, causal parser, donor posterior, framing and standard backends |
| `optimized/crg_core.cpp` | Native implementation of the two context profiles and P/K/I/S/W payload engines |
| `optimized/crg_fast.py` | Snapshot, explicit build, native subprocess control, CRG2 framing, integrity and whole-file selection |
| `block/README.md` | Block format, claimed external tests, synthetic/1KB-prefix measurements and stated limits |
| `block/src/crg.cpp` | Different context parent and optional prefix-matched role-history expert, plus CGR1 framing |
| `block/compress.py` | GCB1 block container, measured per-block codec selection, decode validation and publication |

The arithmetic coders emit actual bytes, include underflow renormalization and
explicit termination/padding, and reconstruct from archives. Both model families
predict from decoded raw bytes. Neither implementation uses FX2's WRT frontend,
statistical bank or pretrained neural model. Their standalone parent is therefore
not a drop-in numerical equivalent or a descendant entitled to FX2's score.

The optimized high-context parent interpolates byte orders zero through six,
with five separate 2^18-slot high-order banks, exact context tags, deterministic
eviction and count halving at 512. The block parent has a shared bounded hash
table and different interpolation/count semantics. Similar descriptions do not
make these two parents identical.

## Differences relevant to the relational hypothesis

| Question | Closed Gamma FX2 realization | Optimized import | Block import |
| --- | --- | --- | --- |
| Coded coordinates | WRT modeled bytes | Original raw bytes | Original raw bytes |
| Donor memory | 64 words per direction | 32 words per direction; page-local | 32 words per direction; page-local |
| Donor selection | Up to four paired recent/older words frozen per epoch | Up to four recent words selected at mention start | All retained donors matching the decoded current word prefix |
| Shared latent donor weights | Within 4,096-modeled-byte epochs | Retained only while the exact selected donor tuple is unchanged | None |
| Outer parent/expert weights | Reset per declared epoch | Persist across the file | Persist within each independently coded block |
| Wrong-donor control | Distinct older words with equal modeled length | ROT13 changes donor spellings | No matched independent/shared/wrong arm set |
| Recursive rules or shared multi-argument programs | Not implemented | Not implemented | Not implemented |

The optimized parser delays title publication until the closing title tag and
clears page memories at page boundaries. Its donor candidates can change between
mentions; changing the tuple resets that binding posterior. Thus file-persistent
outer weights do not imply file-persistent argument bindings.

The block expert uses the decoded word prefix to enumerate matching donor
continuations, adds mass to their next bytes, and normalizes that distribution
through the next bit's decoded prefix. This is a concrete alternative to starting
a small set of exact copies at each word boundary. It does not introduce a
persistent latent argument shared across mentions. Independent block coding also
discards context and relational history between blocks (at most 1 MiB each).

The optimized `auto` branch explicitly tries stored, Deflate, LZMA and the native
**parent only**. Its default invocation does not evaluate shared bindings. The
block `auto` branch compares actual stored/Deflate/Bzip2/LZMA payloads and, when
provided a native binary, both native modes. It verifies the selected inverse.
Minimum-size selection is scoped to the tested alternatives under the fixed
container; all delivered decoder implementations still need accounting.

## What the supplied measurements support

The optimized README reports a reduction from 418,152 to 268,174 archive bytes
on a 1MB interval of a Gensim Wikipedia XML fixture when replacing its basic
order-2 parent with its order-6 parent. It reports shared and independent arms
both at 268,174 bytes there. Shared relations save two development bytes, tie
independent bindings and add no gain on either separate population. This supports
the reported baseline improvement, not a demonstrated persistent-binding gain.

The block README's 250KB and 1MB examples are generated XML. Its only reported
canonical enwik9 population is 1,000 bytes. Role history ties its native parent
on the listed examples; generic codecs win the selection. Those populations are
not Gamma's three retained populations and their sizes cannot be used as a
head-to-head FX2 comparison or a corpus forecast.

These are claims attributed to the supplied READMEs. Their referenced benchmark
scripts, original tests, proofs and evidence bundles were not imported, so this
review does not reproduce those reported runs. Source license annotations alone
do not supply the missing authorship/package provenance records.

## Independent checks performed here

[The retained test harness](../tests/test_crg_import_20260920.py) passes 76 checks
using only empty, binary, repeated XML and malformed synthetic inputs:

- Both native sources compile with GCC, C++17, warnings as errors and undefined-
  behavior sanitization.
- Forty optimized cases cover both profiles, all five arms and four inputs.
  Python/native archives match exactly; each decoder reads the other's archive;
  decoded bytes and fresh native archive repeats match exactly.
- Twenty-eight block cases cover four inputs and all six explicit codecs plus
  auto. A 257-byte block policy exercises partial and multiple blocks. Inverse,
  repeat and actual minimum-payload selection checks pass.
- Eight rejection cases cover corruption, truncation, trailing bytes and output
  caps for both bundles; failures publish no final output.

Original input paths are removed before decode in the roundtrip checks. This is
not a restricted-filesystem proof or an independent full-state witness. The
provided READMEs' separate 33-test and 23-test suites were not available; the 76
checks above are new, explicitly scoped tests of the imported bytes. No canonical
corpus, training, installation, full-package accounting or prize qualification
was performed. Fixture identities, source identities, command and test output
are in the [review receipt](../operations/evidence/crg_import_review_20260920.json).

## Assessment and disposition

The concrete contributions are inspectable standalone context codecs, a Python/
C++ reference pair, two explicit causal history policies and measured codec
selection. They are useful research components. Their strongest reported result
comes from a conventional stronger parent; their own measurements do not show a
shared-binding advantage that survives the controls and separate populations.

Keep the imports as separately identified reference implementations. Preserve
the closed FX2 result and its parked decision. This read-through identifies no
measured cause overturning that result and selects no successor mechanism or
corpus launch. The 96M objective and 95M stretch remain; full-corpus score is
unknown. Component intent and evidence authority are preserved.
