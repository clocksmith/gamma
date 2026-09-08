# Third-Party Notices

Status: **INTEGRATED IN THE CURRENT SOURCE TREE** — license texts are in
`licenses/`; the recorded canonical build is bound by `build-manifest.tsv`
(`candidate_wrapper_sha256 d11595b6...`).

This is the final attribution notice for the current source tree. It is not
legal advice. The detailed source audit is
`docs/SUBMISSION-ATTRIBUTION-AUDIT.md`.

## Confirmed Components

| Component | Confirmed attribution | License signal | Source evidence |
|---|---|---|---|
| fx-cmix / fx3-cmix lineage | Kaido Orav | Repository GPL-3.0 | Candidate snapshot `README.md`, `.git/config`, and root `LICENSE` |
| Concrete fx3-cmix source anchor | Kaido Orav repository lineage | Repository GPL-3.0 | Commit `220e174add056f49bbe14f26c926cd1878d0de7d`; two frozen-local blocks are byte-identical |
| fxcm / fxcm_v26 | Kaido Orav, 2024-2025 | GPL-2.0-or-later file notice | `src/models/fxcm_v26.cpp:1-24` |
| cmix-lex integration | Ibrahim Marcouch, 2026 | Preserved inside the fxcm_v26 file notice | `src/models/fxcm_v26.cpp:1-8` |
| fxcmv1 | Kaido Orav, 2024 | GPL-2.0-or-later file notice | `src/models/fxcmv1.cpp:1-17` |
| LLVM / ATen utility code | LLVM Project and ATen modification lineage | Apache-2.0 WITH LLVM-exception | `src/ds/SmallVector.h`, `src/ds/SmallVector.hpp`, `src/ds/AlignOf.h` |
| emhash | Huang Yuanbing and bailuzhou | MIT header notice | `src/ds/emhash_map.hpp`, `src/ds/emhash_set.hpp` |
| paq8px v208 | Complete copyright-holder and contributor lists preserved in `licenses/PAQ-FAMILY-NOTICES.txt` | GPL-2.0-or-later in the pinned README | Commit and five file hashes in `docs/paq-family-source-reference-20260722.tsv` |
| paq8hp12any | Matt Mahoney, Alexander Ratushnyak, and Przemyslaw Skibinski named as main code authors | GPL in the primary README/source | Primary ZIP and extracted-file hashes in `docs/paq-family-source-reference-20260722.tsv` |
| paq8l | Copyright holders listed in the primary `paq8l.cpp` | GPL-2.0-or-later file notice | Primary ZIP and extracted-file hashes in `docs/paq-family-source-reference-20260722.tsv` |

All existing source headers remain authoritative; this notice does not replace
them.

## Confirmed Non-Identical Adaptations

| Candidate signal | Required before publication | Status |
|---|---|---|
| `fxcm_v26.cpp:2419-3326`, English stemmer | Core `Word` methods, tables, and stemmer steps are range-mapped to pinned paq8px v208 `Word.cpp`, `EnglishStemmer.cpp`, and `EnglishStemmer.hpp`, with local fields, grammar/type tables, exceptions, and integration changes | CONFIRMED STRUCTURAL CORRESPONDENCE - NOT BYTE IDENTICAL |
| `fxcm_v26.cpp:4104-4118`, match-position element | v208 range correspondence confirmed: history count 3 to 4 and `memmove` to fixed four-entry shift | CONFIRMED STRUCTURAL CORRESPONDENCE - NOT BYTE IDENTICAL |
| `fxcm_v26.cpp:6081-6120`, paq8hp12-derived block | `paq8hp12.cpp:2698-2723` correspondence and threshold, model, APM, stream, branch, and weight modifications mapped | CONFIRMED STRUCTURAL CORRESPONDENCE - NOT BYTE IDENTICAL |
| `preprocessor.cpp` and `dictionary.cpp`, paq8l/paq8hp12any/paq8px adaptation | Detection interface, framing, WRT markers/codewords, dictionary loading, word encoding, substring fallback, decode, and case restoration are functionally range-mapped with every local modification class stated | CONFIRMED STRUCTURAL/ALGORITHMIC CORRESPONDENCE - NOT BYTE IDENTICAL |
| Porter2 attribution | Porter2 algorithmic basis through pinned paq8px v208 is confirmed; incorporation of separate Snowball source code is not established | CONFIRMED ALGORITHMIC BASIS - SNOWBALL CODE COPY UNPROVEN |

The detailed machine-readable range and modification map is
`docs/submission-source-range-map-20260722.tsv`, SHA-256
`c1e7ced98a60b308873358a75e85095b7f79f84677de540ca8878dfb075544f8`.

## Files Included In The Final Source Tree

1. The candidate snapshot's complete root `LICENSE` file.
2. The official Apache-2.0 text and LLVM exception in
   `licenses/LLVM-LICENSE.txt` (SHA-256 `8d85c105...afee`).
3. The Snowball BSD-3-Clause text in `licenses/SNOWBALL-COPYING.txt` (SHA-256
   `88080287...a678`) while a separate Snowball source-code incorporation remains unproven.
4. `licenses/PAQ-FAMILY-NOTICES.txt` (`2881 B`, SHA-256
   `4603b1ffd23691af9cf439b1d2f796a9a2260c808e304b4a5ff5fb739f287207`)
   plus this integrated `THIRD-PARTY-NOTICES.md`.
5. The exact source and build scripts used for the submitted binaries.
6. A deterministic manifest binding every source, notice, build input, binary, and
   generated archive by byte size and SHA-256.
7. A modification record naming the responsible author and date for this project's
   changes; no author or prize split may be inferred from the repository alone.

## Publication Gate — status

The notices and exact license texts are placed in this source tree
(`licenses/`, hash-verified against the values above), and the canonical
rebuild is bound to the submitted binaries via `build-manifest.tsv`
(`candidate_wrapper_sha256 d11595b6…`). The license and reproducibility gates
are therefore closed for this tree. Remaining open item before submission:
the explicit authorship/prize-split declaration (see `MODIFICATION-RECORD.md`,
section "Authorship and prize split"). The Snowball caveat above (algorithmic
basis confirmed, code copy unproven) is retained as an honest statement, with
the Snowball license text included defensively.
