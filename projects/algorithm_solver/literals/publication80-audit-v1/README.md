# Publication provenance audit for the live JavaScript 80

2026-10-23. Metadata-only decision preparation under the owner direction relayed
from Mars. **The 80 source lineages are identified; publication of new rewrites
is not cleared.** This audit grants no rights and changes no publication,
qualification, deployment or protected-evaluation gate.

The exact cohort is the [published hash list](../guides-joint80-8-v2/published-8-v1-sources.json)
used by [the bridge freeze](../bits80-bridge-v1/FREEZE.md).
All 80 hashes match the compact rows in the
[scale manifest](../scale-v2/generated/manifest.json), with an original-source
hash chain for every ID. The [per-ID audit](audit.json) contains metadata only:
IDs, URLs, upstream and successor hashes, provenance records and unresolved items.
No program bodies, descriptions, case values, dictionaries or sequences were
opened or copied. No experiments, retrieval queries, source execution,
publication, catalog/claim writes or protected/final-heldout access occurred.

| Lineage established by existing metadata | Count | Rights evidence and remaining gap |
| --- | ---: | --- |
| LCD reference-derived | 60 | Pinned HF card declares Apache-2.0; linked GitHub license says MIT. Existing records explicitly leave source-specific scope unresolved. |
| Owner-supplied agent candidates | 19 | Three immutable source seals hash-match for all 19. Reference attribution does not establish copied origin, independent authorship or publication permission. |
| doocs reference-derived, ID 1046 | 1 | Pinned JavaScript upstream path/hash and normalized-source hash resolve the vague five-family reference. CC-BY-SA-4.0 and the README's separate commercial-authorization wording require a recorded publication determination. |
| Matching compact/original lineage metadata | 80 | Hash identity is established, not a new rights grant. |
| Recorded shared-style rewrite hashes | 80 | All have passing historical qualification receipts; all differ from the published compact hashes. No release selection is made here. |
| New rewritten sources cleared by this audit | 0 | Owner publication approval remains outstanding; evidence gaps below remain explicit. |

## Provenance findings

The 60 LCD rows come from
[clusters attribution](../clusters-v1/ATTRIBUTION.json). Each pins a selected
reference UID/hash and the HF snapshot
`215604aeed660029df7de2fea5a4d7b6ed476a08`. Their original-source hashes also match
historical cluster manifests. A doocs notice appears in merged metadata, but
that alone does **not** assign doocs terms to these 60 selected references.
The scope of normalization/adaptation is recorded, rather than assumed to erase
upstream rights.

The remaining 20 come from
[additional provenance](../scale-v2/additional-provenance.json): 19 owner-supplied
candidates (IDs 3, 4, 7, 9, 11, 14, 20, 28, 34, 35, 42, 53, 55, 58, 62, 64, 67,
69, 70) and ID 1046. For the 19, hashes of the B01/B02/B03 source seals were checked
without inspecting source bodies. The records distinguish reference material
reviewed for behavior from the origin of the submitted candidate. This audit
preserves that distinction and does not claim clean-room authorship.

ID 1046's additional-provenance row names only an earlier five-family catalog.
The [earlier summary](../../findings/source-corpus-js-py-128-v3/summary.json)
resolves it to doocs JavaScript at
`88c8c2c29f19c186d7cc05c9db17245d9ae3df43`, with explicit-max-heap adaptation and
normalized hash
`e07a28d5bbed83eb8baafc5a66b19eaee96cd6c73d80faaf62d4750efa706ef5`.
That hash equals the scale original. The `lcd:1046` identity in the older record
is a problem identity; it does not make this JavaScript implementation an LCD
source. Its doocs provenance is source-specific.

The [style150 rewrite receipts](../style150-v1/evidence/results.json) provide an
existing 80-ID rewrite inventory, with hashes and recorded qualification. They
are **not** a selected publication package. A later choice among style150,
scale500, item 13 or other successors needs its own exact hash manifest and
lineage/permission review. Correctness receipts do not decide copyright status.

## Primary rights evidence checked

[Retrieval metadata](upstream-checks.json) records URLs, UTC checks and hashes;
no page payload or program source was saved. Six direct requests succeeded.
LeetCode's direct request returned 403; its terms were separately read through
the web tool. The existing archived HF/GitHub notice hashes were also verified.

- The [pinned HF card](https://huggingface.co/datasets/newfacade/LeetCodeDataset/raw/215604aeed660029df7de2fea5a4d7b6ed476a08/README.md)
  declares Apache-2.0 and describes a Python problem dataset. The
  [GitHub license](https://raw.githubusercontent.com/newfacade/LeetCodeDataset/182cd19fd53161efd70a1ef074fe1056b659bfa3/LICENSE)
  is MIT with a 2025 newfacade notice. The latter is now pinned to the Git commit
  resolved during this audit; it is not asserted to be the HF snapshot's Git
  counterpart. Neither difference is silently treated as dual licensing.
- The [pinned doocs README](https://raw.githubusercontent.com/doocs/leetcode/88c8c2c29f19c186d7cc05c9db17245d9ae3df43/README_EN.md)
  declares CC-BY-SA-4.0 and separately asks commercial reprinters to obtain
  authorization. Its [license text](https://raw.githubusercontent.com/doocs/leetcode/88c8c2c29f19c186d7cc05c9db17245d9ae3df43/LICENSE)
  matches the archived notice. The [official CC summary](https://creativecommons.org/licenses/by-sa/4.0/)
  permits commercial sharing/adaptation under its conditions. Preserve both
  upstream statements and resolve their application to ID 1046; do not recast
  CC-BY-SA itself as a noncommercial license.
- The [LeetCode terms](https://leetcode.com/terms/) address platform content,
  ownership and notices. They do not supply an established redistribution grant
  for this candidate package. Problem descriptions, examples, original solutions
  and newly authored code must not be collapsed into a single rights category.
  This audit neither copies problem text nor decides its legal status.
- If Apache-2.0 applies, its [redistribution conditions](https://www.apache.org/licenses/LICENSE-2.0)
  include preserving the license and relevant notices, marking modifications and
  handling applicable NOTICE content. If MIT applies, retain its required
  copyright/permission notice. If CC-BY-SA applies, record attribution, license
  link, modifications and the appropriate ShareAlike terms. These are conditional
  packaging requirements, not a determination that any particular grant applies.

## Concrete open items for the owner decision

| Code | Applies to | Evidence still needed before approving a new package |
| --- | --- | --- |
| G1 | All 80 | Explicit owner authorization naming the new source hashes, intended distribution and publication scope. Prior permission for compact sources does not cover distinct rewrites automatically. |
| G2 | All 80 | Select the actual release files. Bind each to predecessor/reference hashes, transformation/authorship records and its qualification receipt. The style150 inventory is one candidate inventory, not approval to choose it. |
| G3 | 60 LCD-derived rows | Establish which upstream grant covers the selected reference files and subsequent adaptations; retain evidence resolving HF/GitHub scope and any third-party rights. Availability and Gamma's MIT license do not answer this. |
| G4 | 19 owner-supplied candidates | Record author/agent provenance, source inputs or reused code, rights-holder authority and scope of permission for the exact rewritten artifacts. Existing seals prove identity, not these rights assertions. |
| G5 | ID 1046 | Resolve the doocs-specific grant/README wording for the intended distribution; record required attribution, modifications and derivative-license treatment, or a distinct authorized replacement with a new lineage. No automatic replacement is performed. |
| G6 | All selected release artifacts | Produce a file-level attribution/license/notice package and verify it against the approved manifest. Treat descriptions, examples and helpers separately if later included; none is approved through this source-only audit. |

These are documentary gaps in the inspected evidence, not a conclusion that the
sources are unpublishable. The owner can approve a complete package only after
the applicable gaps are resolved; an owner's operational approval cannot itself
supply missing third-party rights.

## Reproduction and boundaries

Run `python3 projects/algorithm_solver/literals/publication80-audit-v1/build_audit.py`.
The builder reads only named metadata manifests/notices and hashes three source
seal metadata files; it never imports experiment loaders or reads solution/test
files. It asserts the exact 80-ID partition, all compact/original hash links,
all rewrite receipts and the 60/19/1 split. It writes only `audit.json`.
Upstream checks are a dated receipt, not silently refreshed by that command.

Validation: successful deterministic rebuild, Python syntax/import check,
80/80 metadata joins, 19/19 seal checks and two archived-notice hash checks.
No numerical, runtime or publication qualification is claimed.
Component: algorithm-solver literal research reporting. Intent preserved;
no component or authority boundary changed. No frozen historical artifact edited.
