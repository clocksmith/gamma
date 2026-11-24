# BITS research map

Start here to choose one task. The [historical index](INDEX.md) records lineage,
and cohort reports remain the authority for numerical claims.

| Lane | First entry | What it establishes |
| --- | --- | --- |
| Current result | [Fixed-source comparison v1](fixed-source-v1/RESULTS.md) | Frozen run of the [protocol](FIXED_SOURCE_PROTOCOL_V1.md) on 400 paired Python and JavaScript solutions: verified dictionaries, certified bounds, shared against separate. In-sample only. |
| Next experiment (unrun) | [Unrestricted fixed-source retest](FIXED_SOURCE_PROTOCOL_V2.md) | Same pinned source, unrestricted substrings versus the matched historical rule. No results until a new freeze, run and independent verification. |
| Representation baseline | [Pure 7/8-bit literal comparison](pure-literal-compare-v1/README.md) | Exact reconstruction of 400 known development programs per language, with separate payload, packet and dictionary accounting. Its exposed validation set is not a fresh holdout. |
| Transfer evidence | [Witness length and unseen transfer](witness-length-sweep-v1/RESULTS.md) | Frozen byte-level sweep and replay on four train/test pairs. `jointBest` can use singletons; `greedyDP` is fragment-heavy, not singleton-free. No recorded multi-byte transfer lift in these arms. |
| Capacity evidence | [Capacity reproduction manifest](bits-reproduce-v1/MANIFEST.md) | Rechecks stored witnesses and certificates; it does not repeat search or establish timings. |
| Editor and promotion | [Promotion contract](BITS_PROMOTION.md), [legacy Shared7](demo/README.md) | 256one owns the live editor. Gamma owns experiment data and verification. Legacy profiles are needed for replay even after they leave the picker. |
| Previous research | [Historical index](INDEX.md), [pilot](README.md#historical-pilot-joint-source-and-vocabulary-optimization) | Joint rewriting, counted fragments/macros, staged searches and null results; these are not the active comparator by default. |

## Archive in place first

Do not rename or remove existing experiment folders on the basis of age. Frozen
checksums, embedded relative paths, Git-source pins and external citations
cross this tree. Treat old evidence as closed for new output, not disposable.
For example, the reproduction manifest requires the `matched80` Git object and
checks several sibling folders, and the length sweep uses `witness-scaling-v1`
cohort identities. For lookup only, use the map above rather than placing another
copy of a report or source tree here.

For new work, keep reusable code separate from each version's immutable inputs,
checksums, small summary, and independent checker. Put scratch outputs and bulk
candidate logs outside Git. To move an old folder later, first inventory all
checksums, verifier inputs and external links, then replay at the original pin
and show that the same entry points work after the move. Keep the old revision
addressable. Never rewrite old manifests or delete raw evidence to shrink a tree.
