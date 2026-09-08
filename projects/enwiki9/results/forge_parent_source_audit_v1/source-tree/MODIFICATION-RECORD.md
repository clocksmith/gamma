# Modification Record — forge-cmix (Hutter Prize submission)

Responsible author: **Dirk Nesner** (assisted by an AI research lab pipeline;
all changes reviewed and released under his responsibility).
Record date: 2026-07-23. License of this work: GPL (see root `LICENSE`;
all inherited file headers remain intact, see `THIRD-PARTY-NOTICES.md`).

Base: fx2-cmix lineage by Kaido Orav (GPL-3.0 repository), source anchor
commit `220e174add056f49bbe14f26c926cd1878d0de7d`, plus the fxcm_v26 model
family (Kaido Orav 2024–2025) as integrated by cmix-lex (Ibrahim Marcouch,
2026, GPL-2.0-or-later file notices preserved).

## Changes made in this project (vs. the base above)

| # | Change | Description |
|---|---|---|
| 1 | fxcm_v26 integration | Port of the fxcm_v26 model into this tree's predictor stack (namespace-separated; file notices preserved). |
| 2 | compact23 | Context-output reduction: group mask 23, 403 configured predictor outputs (down from the full set) to cut model work and memory. |
| 3 | auxmatch | One auxiliary match-model output enabled (aux mask 1). |
| 4 | elision | Elision of redundant per-byte model work bound by a preregistered provenance chain (see evidence bundle). |
| 5 | cells270 | LSTM byte-mixer resized to 270 cells. |
| 6 | anon-THP runtime | Anonymous transparent-huge-pages advisory wrapper compiled in (`FX3_ANON_THP`), with status markers written to stderr for audit. |

The exact cumulative source diff of these changes is bound by
`source_patch_sha256 = d19eed8e2e9309f92ad6d16dd4111b4244c2c6e38031085b0cc58552726dcaa0`
(see `build-manifest.tsv`), and the recorded canonical build produced the
submitted compressor wrapper byte-for-byte:
`candidate_wrapper_bytes = 462290`,
`candidate_wrapper_sha256 = d11595b697a3a932c343aabb16171d289fa2dc2b4e1d3423234e9fe7a88294fd`.

## Submission binding

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `cmix` (compressor executable) | 462.290 | `d11595b697a3a932c343aabb16171d289fa2dc2b4e1d3423234e9fe7a88294fd` |
| `archive9` (self-extracting archive; running it with no options restores `enwik9_uncompressed`) | 109.079.791 | `3fea5770bda262650734b6705fa1cda8c5b4f1f7d4eab645c3a6ccf5ed95c90c` |
| Total S | **109.542.081** | — |

Independent-of-runner, fail-closed post-run result audit:
`PASS_INDEPENDENT_1GB_LOSSLESS_LEGAL_AUDIT` (27 automated checks; lossless
restore of enwik9, sha256
`159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`;
normalized time products 67 698.6 / 68 162.1 < 70 000 at Geekbench 5
single-core 1478). See the evidence bundle accompanying the submission.

## Authorship and prize split

Responsible submitter: Dirk Nesner. This work builds on GPL-licensed prior
work whose algorithmic authors are named above and in
`THIRD-PARTY-NOTICES.md` — in particular Kaido Orav (fx2-cmix lineage,
fxcm_v26 model family) and Ibrahim Marcouch (fxcm_v26 integration as
published in cmix-lex).

Prize-division instruction submitted on 2026-07-27: one third to Dirk Nesner,
one third to Kaido Orav, and one third to Ibrahim Marcouch. Kaido Orav and
Ibrahim Marcouch were contacted separately on 2026-07-27 with the same open
request to state the shares they consider fair. Their confirmations or
counterproposals are pending at the time of submission. This proposed
division is not represented as their agreement. No prize payment is requested
before all authors have agreed to a final division; any mutually agreed
replacement will be reported promptly to the Prize committee.
