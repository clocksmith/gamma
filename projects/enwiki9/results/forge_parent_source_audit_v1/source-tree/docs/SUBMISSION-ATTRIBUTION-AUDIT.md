# Provisional Attribution Audit

Status: **SOURCE MAPPING COMPLETE - package integration and clean rebuild pending**

Audited snapshot:
`/home/coolblack/hutter-fxcm-v26-auxmatch-anon-thp-build-20260720/src`

This is an evidence inventory, not a legal conclusion. The final corresponding-source
package must preserve every applicable notice and include verified upstream license texts.

## Confirmed Snapshot Evidence

| Component | Snapshot evidence | Attribution or license signal |
|---|---|---|
| fx3-cmix lineage | `README.md:1-2`, `.git/config:8-10` | Updated fx-cmix lineage; origin `https://github.com/kaitz/fx3-cmix.git` |
| fxcm/fxcm_v26 | `src/models/fxcm_v26.cpp:1-24` | Kaido Orav, 2024-2025; GPL version 2 or later |
| cmix-lex integration | `src/models/fxcm_v26.cpp:1-8` | Ibrahim Marcouch, 2026 |
| fxcmv1 | `src/models/fxcmv1.cpp:1-17` | Kaido Orav, 2024; GPL version 2 or later |
| Repository license | `LICENSE:1-3` | GNU GPL version 3 text |
| LLVM/ATen SmallVector | `src/ds/SmallVector.h:1-18`, `src/ds/SmallVector.hpp:1-15` | Apache-2.0 WITH LLVM-exception; ATen modifications identified |
| LLVM/ATen AlignOf | `src/ds/AlignOf.h:1-15` | LLVM code modified for ATen; references `LICENSE.TXT` |
| emhash | `src/ds/emhash_map.hpp:1-22`, `src/ds/emhash_set.hpp:1-22` | MIT; Huang Yuanbing and bailuzhou; ktprime source URL in headers |
| PAQ-family preprocessor | `src/preprocess/preprocessor.cpp:1` | Adapted from paq8l, paq8hp12any, and paq8px |
| PAQ/Porter-derived model code | `src/models/fxcm_v26.cpp:2418-2420,4104-4105,6081` | Porter2, paq8px v208, and paq8hp12 derivation comments |

The snapshot contains only `LICENSE` and `README.md` among files conventionally named
`LICENSE*`, `COPYING*`, `NOTICE*`, or `README*`. Its README lists Kaido Orav but does
not list the cmix-lex integration author named in `fxcm_v26.cpp`.

## Verified Primary Upstream References

| Component | Primary source | What it establishes | Remaining check |
|---|---|---|---|
| LLVM | `https://llvm.org/LICENSE.txt` | Current Apache-2.0 WITH LLVM-exception text referenced by the SmallVector headers | Include the exact license text in the published source package |
| Snowball/Porter2 | `https://snowballstem.org/license.html` | Snowball software is generally BSD-3-Clause and credits Martin Porter and Richard Boulton | Prove whether the incorporated implementation is Snowball code or a PAQ-derived rewrite before assigning this license to the copied block |
| PAQ family | `https://www.mattmahoney.net/dc/paq.html` | Matt Mahoney's PAQ history identifies paq8l and paq8hp12any lineage and distributes PAQ sources under GPL | Primary archives are pinned below; finish the local range and modification map |
| paq8px | `https://github.com/hxim/paq8px` | The upstream project identifies Jan Ondrus, Marcio Pais, and Zoltan Gotthardt and declares the program free under GPL | v208 is pinned below; finish file-level correspondence and modification mapping |
| fx-cmix | `https://github.com/kaitz/fx-cmix` | GPL-3.0 repository and prior fxcm lineage | Preserve its license, notices, and modification history |
| fx3-cmix | `https://github.com/kaitz/fx3-cmix/commit/220e174add056f49bbe14f26c926cd1878d0de7d` | Concrete upstream `fxcmv1.cpp` anchor for two byte-identical blocks in the frozen local source | Candidate remains a later modified branch; do not claim whole-file identity |

These references narrow the likely license families but do not replace a file-level source
comparison. In particular, the local wording "based on Porter2" and "mostly from paq8px"
does not by itself prove which upstream implementation or revision was copied.

## Pinned paq8px v208 Reference

The upstream release name `paq8px_v208` is an untagged Git commit, not a published
Git tag:

| Field | Verified value |
|---|---|
| Repository | `https://github.com/hxim/paq8px` |
| Commit | `d5d3af875f00a073023eeb081762f839ed19c9b8` |
| Subject | `paq8px_v208` |
| Author and committer | Zoltan Gotthardt `<gotty@freemail.hu>` |
| Commit time | `2023-02-22T23:06:18+01:00` |
| `README` SHA-256 | `a8bfce7d1ce8f3fcb68cca69cf91942e76a42cf3013829423dce1f99152aed4f` |
| `text/EnglishStemmer.cpp` SHA-256 | `8eb023bc3210d1a9017f55e836f44090ebbfed16717081de59374ebad7d55825` |
| `text/Word.cpp` SHA-256 | `cb5dd498747a8c6b26053a64e119f624b94d841459a5f416a62856ab5d9c5605` |
| `model/MatchModel.cpp` SHA-256 | `c4a94eb0c8734e202339d4294ae58928a643f6f442b8b09dc6af4fec67f84b0a` |
| `HashElementForMatchPositions.hpp` SHA-256 | `b89c8623e05f6d37da4ee4b3630495cb0dde72b38249c602ba14424f00f72c0d` |

The pinned README names the PAQ8PX contributors and states GPL-2.0-or-later. The
candidate's `fxcm_v26.cpp:2419-3326` has now been compared against the pinned v208
`Word.cpp:1-121` and `EnglishStemmer.cpp:4-574` full texts. Its core `Word` methods and
the region, prefix, superlative, and Porter2 step 0-5 sequence correspond structurally,
while the candidate adds local fields, hashes, type/suffix flags, prefixes, exceptions,
and integration changes. The commit-bound `EnglishStemmer.hpp:13-116`, SHA-256
`1642e349b3717fa8e331db8718201768e7ad2d359be9ee4035fe6ff615f24816`, also maps the
candidate vowel, suffix, and exception tables at lines `2560-2796`, with local grammar
lists, type tables, and exception-value changes. This confirms paq8px/Porter2 as the
algorithmic basis; it does not establish a copy of Snowball source code.

The candidate's `fxcm_v26.cpp:4104-4118` maps to v208
`HashElementForMatchPositions.hpp:5-13`: history grows from three to four positions and
`memmove` becomes a fixed four-entry shift. Candidate lines `4273-4276` similarly replace
the v208 `MatchModel.cpp:24-35` update with a fixed small shift. These are confirmed
range-level structural correspondences, not byte identity. The complete machine-readable
map is `docs/submission-source-range-map-20260722.tsv`, SHA-256
`c1e7ced98a60b308873358a75e85095b7f79f84677de540ca8878dfb075544f8`.

## Pinned PAQ And fx3-cmix References

The primary PAQ archives and a concrete fx3-cmix source anchor are bound in
`docs/paq-family-source-reference-20260722.tsv`, SHA-256
`e0d3c609d1c8d0daf4e143d3948ffcb30aa41ff2df204a3ccbe42940592b76c0`.

| Reference | Verified source and hash | Confirmed correspondence |
|---|---|---|
| fx3-cmix `fxcmv1.cpp` | Commit `220e174add056f49bbe14f26c926cd1878d0de7d`; file SHA-256 `3b81f4b7903fb3e81a2c345726626fa19b8d62ac610bcf7b8d141633040f9274` | Upstream lines 3366-3653 and frozen-local lines 3406-3693 are byte-identical (SHA `efe9d319...eed0`); the paq8hp12-labelled blocks at upstream 4756-4795 and local 4826-4865 are also byte-identical (SHA `bafc4b91...d3c1`) |
| paq8hp12any | `https://mattmahoney.net/dc/paq8hp12any_src.zip`; ZIP SHA-256 `bd59419f9ad950771c9d591332cc55914d8db05200601be50f5595f04c976eb8` | README states GPL and names Matt Mahoney, Alexander Ratushnyak, and Przemyslaw Skibinski as the main code authors; `paq8hp12.cpp` and `textfilter.hpp` hashes are recorded in the manifest |
| paq8l | `https://mattmahoney.net/dc/paq8l.zip`; ZIP SHA-256 `fb72db122f89faedcc729fe1e3324cac57c9c48903e72107c8350cdbe5e374cf` | `paq8l.cpp` SHA-256 `03273911...baa8` contains its GPL-2.0-or-later notice and copyright list |

The candidate's `fxcm_v26.cpp:6081-6120` maps structurally to
`paq8hp12.cpp:2698-2723`: failure history, `tri`/`trj` correction, APM cascade, and the
failure-dependent mixture remain. The candidate changes the fixed `1820` threshold to
`e_l[x.bpos]`, uses local model/APM/context objects, adds streams and a failure branch,
and changes final weights from `5/11` to `7/9`. The local preprocessor maps its dispatch
and framing to `paq8l.cpp:2847-2940,3034-3075`. The previously omitted
`src/preprocess/dictionary.cpp` is now mapped by functional range: markers and variable
codewords to `textfilter.hpp:20-26,824-896`, codebook loading to
`1577-1592,1631-1768`, word encoding and substring fallback to
`962-1089,1007-1038,3036-3220`, and decode/case restoration to
`1092-1183,3475-3664`. Candidate hashes are `52e5ae9d...97af9` for
`preprocessor.cpp` and `c0c3dcbf...1501f` for `dictionary.cpp`; both match the frozen,
control, and AUX-Match source copies. These are confirmed non-byte-identical structural
or algorithmic correspondences, not claims of whole-file identity with the PAQ archives.

The exact official LLVM and Snowball license texts and the confirmed PAQ-family notices
are integrated in `licenses/` and bound by the final `SOURCE-MANIFEST.tsv`.
`licenses/LLVM-LICENSE.txt` is required by the embedded SPDX headers. The Snowball
COPYING file is included conservatively: the Porter2 algorithmic basis through PAQ8PX
is confirmed, but including it does not assert that Snowball source was copied. The
`licenses/PAQ-FAMILY-NOTICES.txt` (`2881 B`, SHA-256
`4603b1ffd23691af9cf439b1d2f796a9a2260c808e304b4a5ff5fb739f287207`)
preserves the pinned PAQ8PX, PAQ8L, PAQ8HP12any and TextFilter/WRT attribution and GPL
signals, including the complete PAQ8PX copyright-holder list.
`THIRD-PARTY-NOTICES.md` is the integrated final notice; the root GPL-3.0
license and inherited GPL-2.0-or-later file notices are all preserved.

## Integration Status

1. The LLVM, PAQ-family, and conservative Snowball license files are present
   in `licenses/`.
2. `THIRD-PARTY-NOTICES.md` names Kaido Orav, Ibrahim Marcouch,
   fx-cmix/fx3-cmix, LLVM/ATen, emhash, and the confirmed PAQ/Porter sources.
3. Existing source headers are preserved and this project's changes and date
   are recorded in `MODIFICATION-RECORD.md`.
4. `build-manifest.tsv` and `canonical-build.log` bind the canonical build to
   the submitted compressor wrapper; `SOURCE-MANIFEST.tsv` binds the final
   source-package contents.

The remaining pre-submission item is not a missing license file: the
authorship/prize-division declaration required by the Hutter Prize rules must
be agreed and inserted as described in `MODIFICATION-RECORD.md`.
