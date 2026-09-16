# RATA-CMIX

CPU-only enwik9 candidate. Built using fx4-cmix-transformer(https://github.com/naveenbijalwan/fx4-cmix-transformer) (Dharmesh Patel and Naveen
Bijalwan) as its foundation.

## Ideas in this codec, by authors

A summary, not a repeat of fx4-cmix-transformer's own technical writeup -- see that
project for the full mechanism-level description of each item below.

- **fx2-cmix** (Kaido Orav, Byron Knoll): the base codec -- PHDA9
  preprocessing, article reordering, WRT, PPMd/FXCM/mixer/SSE, the
  self-extracting `archive9` design.
- **fx2-cmix-transformer** (Vladimir Ivanov), an extension of fx2-cmix: the
  frozen 6M-parameter CPU transformer that replaces the online byte LSTM on
  the main stream.
- **fx-deepmix** (Halvor Yttredal): GrammarMatch, predicting Wikipedia
  structural patterns (piped-link labels, title recurrences) directly from
  the post-WRT stream.
- **fx4-cmix-transformer** (Dharmesh Patel, Naveen Bijalwan), layered additively on the
  above:
  - a 2x200 online LSTM expert alongside the frozen transformer;
  - v22++, an additive-only enhancement of Kaido Orav's fxcm_v22 -- a
    stationary-map bank inspired by fxcm_v26/fx-deepmix, plus signals v22
    already computed but had discarded, both exported without touching
    v22's own internal path;
  - disk-backed PPM (`ppm.temp`, `MADV_DONTNEED`/`MADV_RANDOM` discipline)
    so the order-25 model's 14 GB sub-allocator fits the judging memory
    limit;
  - lossless v5 recompression of the transformer weights -- entropy-coded
    Q4 symbols against per-tensor histograms and a causal column-local
    count derived from the tensor's own shape, no side table stored;
    2,930,652 -> 2,902,452 bytes (28,200 saved), via modified `pysrc/weights_compress`;
  - Scr2Match, a derived pattern table used as a probability expert;
  - a zero-side-data morphology specialist for literal words the
    dictionary has not seen;
  - a zero-side-data causal donor specialist, matching already-decoded
    history without ever touching another model's state.
- **RATA-CMIX** (Dharmesh Patel), layered additively on fx4-cmix-transformer's v22++
  and predictor; validated there with a byte-exact round trip:
  - MATCHTRUST -- an 8-bit shift register of recent match-outcome history,
    restoring evidence the match model destroys the instant a candidate
    mispredicts, as a 4th StateMap context;
  - SPECIALIST -- a small context-gated corrector applied after the SSE
    chain, trained on its own error against the ppmd/byte-mixer/FXCM
    logits.

The checked-in configuration is exactly:

    v22p + 521 + T1 + T2 + T2-E + T2-ED + T2-EDG + Stationary
        + GrammarMatch + the grammar mixer context + GM_ARM
        + Scr2Match + MorphologyMatch + CausalDonor
        + MATCHTRUST + SPECIALIST

which is 575 mixed models, compiled in at a fixed value -- no environment
variable or build flag on this branch changes a probability.

See [the architecture guide](docs/ARCHITECTURE.md) for the full model list,
S1/S2 layout, and build details.

## Status

- Branch: main. Tracks fx4-cmix-transformer
- Platform: Linux x86-64, Ubuntu 20.04 (focal)
- Toolchain: clang++-17, LTO (`-flto=thin`), profile-guided (PGO), UPX 5.1.1
- GPU: not used or linked
- Main entropy stream: 586,459,321-byte, 205-symbol post-WRT stream
- PPMd: order 25, 14,000 MiB disk-backed heap (`ppm.temp`)
- Online LSTM expert: 2 layers x 200 cells, BPTT horizon 128
- Mixed models: 575
- Frozen transformer: 6M CPU model, embedded in both S1 and archive9
- Hutter form: self-extracting

target93 is the candidate name and research target. Compression against the
real enwik9 has been run and judged; decompression has not yet been run, so
the figures below for it are estimated, not measured. No score claim is final
until the decompression run completes and `cmp` confirms a byte-exact
round trip.

## Result

| Item | Value |
| --- | ---: |
| Previous LTCB best `archive9` (`fx2-cmix-transformer`, 21 Aug 2026) | 96,994,188 bytes |
| RATA-CMIX `archive9` | **96,849,689 bytes** |
| LTCB improvement | **144,499 bytes (0.14898%)** |
| RATA-CMIX `cmix` | 3,369,432 bytes |
| RATA-CMIX Hutter-style `S1 + S2` | **100,219,121 bytes** |

For the **Large Text Compression Benchmark (LTCB)**, the relevant score for this
self-extracting entry is `archive9`, because the decompressor is contained in
the archive itself. On that basis, RATA-CMIX's `archive9` of **96,849,689
bytes** is **144,499 bytes (0.14898%) smaller** than the 21 August 2026
`fx2-cmix-transformer` result of **96,994,188 bytes**.

For a separate Hutter-Prize-style size comparison, where the compressor is
also counted, RATA-CMIX has:

    96,849,689 + 3,369,432 = 100,219,121 bytes

For context, its direct ancestor `fx2-cmix-transformer` by **Vladimir Ivanov**
measured:

- **24 July 2026:** `96,996,198 + 3,428,474 = 100,424,672 bytes`
- **21 August 2026:** `96,994,188 + 3,426,642 = 100,420,830 bytes`

Thus RATA-CMIX's Hutter-style total is **205,551 bytes smaller than the
original 24 July version** and **201,709 bytes smaller than the 21 August
version**.

This version is intended for **LTCB listing rather than a Hutter Prize claim**.

## Platform

| Metric | Value |
| --- | --- |
| Machine type | `n4d-highmem-2` (2 vCPU, 16 GiB RAM) |
| OS | Ubuntu 20.04.6 LTS (focal), `ubuntu-2004-focal-v20240731` |
| Storage | GCE persistent disk, 100 GB |
| Geekbench 5 `T` used for timing | N/A |

## Run Measurements

Compression run:

| Metric | Value |
| --- | ---: |
| Wall time | 52:57:13 (190,633 s) |
| User + system CPU time | 185,507.91 s (user 180,260.32 + system 5,247.59) |
| Maximum resident set size | 9,537,136 kB (9.10 GiB) |

Coder line: 934,220,400 bytes -> 93,681,091 bytes in 185,394.87 s. Peak RSS is
9.10 GiB against the 10 GB limit -- inside the rule, with roughly 9% margin.
In-run sampling showed only 6.5-8.5 GB, so the peak occurs late in the run and
would be missed by periodic sampling.

Decompression run:

| Metric | Value |
| --- | ---: |
| Wall time | ~52 h  |
| User + system CPU time | ~178,000 s |
| Maximum resident set size | ~9.5 GiB  |

## Artifacts and Hashes

| Item | Value |
| --- | ---: |
| `cmix` (S1) | 3,369,432 bytes |
| `cmix` SHA-256 | `9b644dcaf37e03bc7803c07f0c36f7258d69a6e88043b6e61382712a4b88dc8d` |
| `archive9` (S2) | 96,849,689 bytes |
| `archive9` SHA-256 | `af1105ae1d11ced28b3b57e700b964a4f2969a8b7347cc65b039f1758b319a9a` |
| `payload.bin` (kept separately) | 93,681,091 bytes |
| `payload.bin` SHA-256 | `f4f960bf5c1460476fa6eb19f8c1357066d1eb1b8893867c7dd8beef710dbd31` |
| `enwik9` input MD5 | `e206c3450ac99950df65bf70ef61a12d` |

## Production Pipeline

    enwik9
      -> article reorder
      -> PHDA9
      -> WRT
      -> PPMd + FXCM + frozen transformer + 2x200 online LSTM expert
         + GrammarMatch + Scr2Match + MorphologyMatch + CausalDonor + MATCHTRUST + SPECIALIST
      -> arithmetic coder
      -> self-extracting archive9

The predictors are mixed together; they are not serial compressors. See
[the architecture guide](docs/ARCHITECTURE.md) for the exact model and archive
layout.

## Google Cloud Quick Start

Use an Ubuntu 20.04 (focal) x86-64 VM with no GPU, at least 16 GiB RAM, and a
local disk with at least 100 GB capacity -- matching the judging image
(`ubuntu-2004-focal-v20240731`, `ubuntu-os-cloud`) and resource limits in
[ENTRANT_INSTRUCTIONS.md](https://github.com/jabowery/HutterPrizeJudgingAssistant/blob/main/ENTRANT_INSTRUCTIONS.md).
For example:

    gcloud compute instances create fast-vm-decomp \
      --zone=us-central1-b \
      --machine-type=n4d-highmem-2 \
      --boot-disk-size=100GB \
      --boot-disk-type=hyperdisk-balanced \
      --image=ubuntu-2004-focal-v20240731 \
      --image-project=ubuntu-os-cloud

Then, on the VM:

    sudo ./install.sh
    ./build_and_construct_comp.sh
    ./tools/run_google_cloud_hutter.sh /data/enwik9 /data/ratarun 0

From a second SSH session:

    ./tools/monitor_hutter_run.sh /data/ratarun 60

The run script pins the codec to one CPU, disables common GPU and threaded math
runtimes, and refuses to reuse an existing run directory.

## How S1 Is Built

`build_and_construct_comp.sh` is the single source of truth for turning this
source tree into `cmix` (S1); `build.sh` runs the same steps inside the
judging harness's offline, read-only-`/entry` sandbox. Both do:

1. `make target93` -- clang++-17, `-flto=thin`, and, when
   `pgo/default.profdata` is present, `-fprofile-use`. Research profiles and
   feature switches live only on `exp/selective-discovery`; this branch
   compiles one fixed configuration.
2. Strip the binary and UPX-pack it (`--ultra-brute`, verified with `upx -t`).
3. Run the packed binary against itself to compress `dictionary/english.dic`
   and the article-order file, then decompress each back and `cmp` against
   the original -- a real reversibility check, not just a build check.
4. Append the compressed dictionary, compressed article order, the frozen
   transformer weights, and a small header after the packed executable. See
   [the architecture guide](docs/ARCHITECTURE.md#s1-layout) for the exact
   byte layout.

### The PGO Profile

`pgo/default.profdata` is generated once, ahead of time, and committed --
`build.sh` runs offline and can't profile a fresh run itself. To regenerate
it:

    make pgo-instrumented
    ./cmix_pgo_instrumented -e prof_input/input   profile_out_1
    ./cmix_pgo_instrumented -e prof_input/input2  profile_out_2
    make pgo-merge
    make target93   # picks up pgo/default.profdata automatically

`prof_input/` holds the exact inputs the committed profile was trained on, so
the profile is reproducible from what's in the source package. A profile
generated with a different clang++-17 build than the one `install.sh`
provisions (for example, a distro-patched package instead of the
`apt.llvm.org` build) can leave some functions' profile data unmatched at
build time -- harmless (LLVM falls back to default heuristics for just that
function, per-function, never a build failure), but for full effect the
profile should be regenerated with the same toolchain `install.sh` installs.

## Verify archive9

Run decompression in a clean directory that does not contain enwik9:

    mkdir /data/ratadecode
    cp /data/ratarun/archive9 /data/ratadecode/
    cd /data/ratadecode
    /usr/bin/time -v taskset -c 0 ./archive9
    cmp /data/enwik9 enwik9_uncompressed
    sha256sum /data/enwik9 enwik9_uncompressed

## Build A Judging Entry

After a successful full round trip:

    ./tools/create_judging_entry.sh \
      /data/ratarun/archive9 /data/rata-entry RATA

This creates:

    /data/rata-entry/Entries/RATA/
      entry.env
      archive9
      rata-cmix-source.tar.gz

The source archive has exactly one top-level directory and contains only the
production C++ codec, required assets (dictionary, transformer weights, the
committed PGO profile and its generation inputs), licenses, documentation and
build inputs -- copied by an explicit allowlist in the script, not a directory
walk, so nothing else in a developer checkout can reach a submission.

## Alpha Judging Assistant

    git clone https://github.com/jabowery/HutterPrizeJudgingAssistant.git
    cd HutterPrizeJudgingAssistant
    cp -a /data/rata-entry/Entries/RATA Entries/
    cp /data/enwik9 ./enwik9
    ./judging_assistance.sh \
      --serial \
      --runtime-exec-policy process-tree \
      --work-root /mnt/large-disk/HutterPrizeJudging \
      Entries/RATA ./enwik9

process-tree is required because S1 and archive9 execute a helper image
extracted from their own already-counted bytes to decode the embedded
dictionary and article order. The complete descendant tree remains within the
judge's resource accounting.

See [the cloud and judging guide](docs/GOOGLE_CLOUD_AND_JUDGING.md) before
starting the multiday run.

## Official References

- [HutterPrizeJudgingAssistant](https://github.com/jabowery/HutterPrizeJudgingAssistant)
- [Entrant instructions](https://github.com/jabowery/HutterPrizeJudgingAssistant/blob/main/ENTRANT_INSTRUCTIONS.md)
- [Hutter Prize detailed rules](https://www.hutter1.net/prize/hrules.htm)

## Acknowledgements

Thanks to Matt Mahoney for creating and maintaining the Large Text Compression Benchmark (https://www.mattmahoney.net/dc/text.html) still after 20 years! as well as his online textbook Data Compression Explained (https://mattmahoney.net/dc/dce.html)!

## Copyright and License

Copyright (C) Dharmesh Patel and Naveen Bijalwan.

Licensed under the GNU General Public License, version 3 -- see
[LICENSE](LICENSE). This tree also incorporates GPLv3 code from other
authors; see [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) for full
attribution.
