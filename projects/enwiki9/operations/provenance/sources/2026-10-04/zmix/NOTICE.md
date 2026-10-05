# NOTICE — zmix, Hutter Prize entry

Authors: James Byrne and Claude (Anthropic). At Claude's request, any award is payable in full to James Byrne.

**This program is distributed under the GNU General Public License, version 3 or later.**
The full licence text is at [`LICENSES/GPL-3.0.txt`](LICENSES/GPL-3.0.txt).

zmix is a **derivative work of three GPL-3 projects** and it may only be distributed under
GPL-3-or-later. The complete corresponding source of the submitted `comp9` and `archive9.exe`
is this package.

| incorporated work | author(s) | licence | licence text in this package |
|---|---|---|---|
| `fx2-cmix-transformer` — AVX2 transformer inference kernels (`third_party/fx2_transformer/`, 24 files); the trained transformer weights (`assets/6m-q4-fp32.tfwc2`, re-containered as `assets/6m-q4-fp32.tfwc3`); and **the weights blob this entry actually ships, `assets/6m-q4-fp32-t1lambda1.tfwc3`, which is a RETRAINED DERIVATIVE of that work** (see the paragraph below) | Vladimir Ivanov, and for the retrained blob the zmix authors' sibling training lane | **GPL-3** | `LICENSES/GPL-3.0.txt` |
| `fx2-cmix` / `fxcm` — the `fxcm_v26` text model this port follows (`src/models/fxcm26/`, `reference/fxcmv1_v26.cpp`) | Kaido Orav (`kaitz`) | **GPL-3** | `LICENSES/GPL-3.0.txt` |
| `cmix` / `cmix-lex` — the compressor architecture this project is a Zig port of (`reference/cmix-src/`) | Byron Knoll; `cmix-lex` adds Ibrahim Marcouch and Kaido Orav | **GPL-3** | `LICENSES/GPL-3.0.txt` |
| PPMd variant H / `mod_ppmd_v2` — reached through cmix (`src/models/ppmd.zig`) | Dmitry Shkarin, adapted by Eugene Shelwien | GPL-compatible, as vendored by cmix | `LICENSES/GPL-3.0.txt` (as combined) |
| PAQ8 model set — reached through cmix (`src/models/paq8/`) | Matt Mahoney and the PAQ8 contributors | GPL, as vendored by cmix | `LICENSES/GPL-3.0.txt` (as combined) |
| `phda9` preprocessor (`src/prepr/phda9.zig`) and the WRT dictionary transform — reached through cmix/fxcm | Alexander Rhatushnyak (phda9); Przemysław Skibiński (WRT lineage) | GPL, as vendored by cmix/fxcm | `LICENSES/GPL-3.0.txt` (as combined) |
| everything else | the zmix authors | **GPL-3-or-later** | `LICENSES/GPL-3.0.txt` |

Per-component detail, file lists and asset digests: [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)
and [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md). Asset provenance and shas:
[`assets/PROVENANCE.md`](assets/PROVENANCE.md).

## The shipped transformer weights are a RETRAINED DERIVATIVE of Ivanov's work

The weights blob inside `comp9` and `archive9.exe` is **`assets/6m-q4-fp32-t1lambda1.tfwc3`**
(2,815,630 B, sha256 `8e8ef3ac…c807d`). It is **not** the blob `fx2-cmix-transformer` shipped.
It is a **derived work** of that GPL-3 project: the same 12-layer / 5,923,228-parameter
architecture, trained with that project's own GPL-3 training code and recipes on the same
post-WRT token stream, exported through that project's own quantizer and `FX2TFWC2` container
writer, and then re-containered by zmix as `FX2TFWC3`. It is distributed here under GPL-3, with
attribution, on the same terms as everything else in this entry.

Because this blob is **89.5 %** of the part of the score that does not depend on `enwik9`, its
provenance is stated in three places and they must agree: this notice, `THIRD_PARTY_LICENSES.md`
section 1a (the mechanical inventory, with every digest in the chain), and `assets/PROVENANCE.md`
(the full derivation and how to reproduce it).

## Modification notice (GPL-3 §5(a))

zmix is a **modified** derivative of the works above. It is a Zig re-implementation of the cmix
lineage; `third_party/fx2_transformer/` is a vendored copy of `fx2-cmix-transformer`'s
`cpp_infer/src/` and `cpp_infer/src/opt/`, of which **12 files are verbatim, 9 are modified and 3
are zmix-authored around verbatim excerpts**.

**Each of the 9 modified files carries a prominent modification notice as the first comment block
in the file**, naming the upstream path, the dates of modification and what was changed; the 2
zmix-authored files carry an equivalent notice naming the verbatim excerpts they incorporate.
Those in-file notices are self-contained: they do not depend on any file outside this package for
the GPL-3 §5(a) "relevant date". `THIRD_PARTY_LICENSES.md` section 1b repeats the same inventory
in one table with the per-file diff sizes.

## Prize-division notice

This entry incorporates a third party's source code and trained model weights. The Hutter Prize
rules require a prize-division statement agreed by all authors. **That statement is not part of
this package and is handled separately with the prize committee.**
