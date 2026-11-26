# BITS research map

Start here to choose one task. The [historical index](INDEX.md) records lineage,
and cohort reports remain the authority for numerical claims.

| Lane | First entry | What it establishes |
| --- | --- | --- |
| Current result | [Fixed-source comparison v1](fixed-source-v1/RESULTS.md) | Frozen run of the [protocol](FIXED_SOURCE_PROTOCOL_V1.md) on 400 paired Python and JavaScript solutions: verified dictionaries, certified bounds, shared against separate. In-sample only. |
| Unrestricted retest | [Fixed-source comparison v2](fixed-source-v2/RESULTS.md) | Frozen run of the [v2 protocol](FIXED_SOURCE_PROTOCOL_V2.md): unrestricted substrings against the matched two-file control, with exact reconstruction and rechecked bounds. In-sample, with no proved optimum. |
| Final measurement, lane closed | [Fixed-source comparison v3](fixed-source-v3/RESULTS.md) | Total encoded size, dictionary and code tables included, for shared and per-language designs against BPE, PathPiece, frequency, GreedTok and LP baselines. The frozen kill bar passed, but the effects are small and predictable from known theory, so BITS closed with a benchmark note. In-sample, no proved optimum. |
| Representation baseline | [Pure 7/8-bit literal comparison](pure-literal-compare-v1/README.md) | Exact reconstruction of 400 known development programs per language, with separate payload, packet and dictionary accounting. Its exposed validation set is not a fresh holdout. |
| Transfer evidence | [Witness length and unseen transfer](witness-length-sweep-v1/RESULTS.md) | Frozen byte-level sweep and replay on four train/test pairs. `jointBest` can use singletons; `greedyDP` is fragment-heavy, not singleton-free. No recorded multi-byte transfer lift in these arms. |
| Capacity evidence | [Capacity reproduction manifest](bits-reproduce-v1/MANIFEST.md) | Rechecks stored witnesses and certificates; it does not repeat search or establish timings. |
| Editor and promotion | [Promotion contract](BITS_PROMOTION.md), [legacy Shared7](demo/README.md) | 256one owns the live editor. Gamma owns experiment data and verification. Legacy profiles are needed for replay even after they leave the picker. |
| Previous research | [Historical index](INDEX.md), [pilot](README.md#historical-pilot-joint-source-and-vocabulary-optimization) | Joint rewriting, counted fragments/macros, staged searches and null results; these are not the active comparator by default. |

## Owner decision, 2026-11-26

From an external review the owner accepted.

- **The contribution is exact certification. Codec superiority is unproven.** The frozen r4 manuscript proves
  110 entries are both enough and necessary for 704 selected three.js files. On A08 the post-hoc defect tree raises
  the lower bound from 69, where the pre-registered method and the baseline both stopped, to 71. A replayed 72-entry
  dictionary leaves the minimum open.
- **Next bet.** On unseen families, test whether checkable trees routinely close gaps that the strongest prior
  bound leaves open, with proof size and verification time frozen as constraints. The pre-registration is being
  written in `capacity-hybrid-certificate-v1/`.
- **Stop.** No tuning on holdouts. A smaller dictionary is not presented as better compression.
- **Codec-claim bar.** Any BITS codec claim needs fresh data, lean-framed zstd and FSST baselines, complete
  accounting of every byte the decoder sees, and a measured p95 lookup latency. The short-record harness's
  golden-byte accounting fixture is the required check (`short-record-decision-v1/STATUS.md`).

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
