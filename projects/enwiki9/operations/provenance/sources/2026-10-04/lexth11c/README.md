# cmix-lex

`cmix-lex` is a Hutter Prize compressor by Ibrahim Marcouch, derived from
[`fx2-cmix`](https://github.com/kaitz/fx2-cmix). It keeps the same
cmix/PAQ-family self-extracting `archive9` pipeline and adds a reversible tail
transform specialized for structured PHDA9 metadata.

This project is not `fx3-cmix`; Kaido Orav used that name for his unpublished
follow-up work.

## Submission Files

Expected files for the final public submission:


[https://drive.google.com/drive/u/0/folders/1oCl3jVF90Dq_AHf33eemB3J3L8EDIKkE](https://drive.google.com/drive/u/0/folders/1oCl3jVF90Dq_AHf33eemB3J3L8EDIKkE)


```text
archive9
cmix
```

SHA256:

```text
3ed9d13e039b08be2a59f90491dd10cd5fb1b9b49f6582b442b79d969221c4e6  archive9
356aeed61ccb2b8ed87e444f02f0fdcca174ca658997f8179c0f6ac56c75b74c  cmix
```

## Result

| Item | Value |
| --- | ---: |
| Previous record `L` | `110,793,128` bytes |
| `archive9` | `109,190,109` bytes |
| `cmix` | `459,938` bytes |
| Total `S = archive9 + cmix` | `109,650,047` bytes |
| Improvement `1 - S/L` | `1.0317%` |
| Bytes below previous record | `1,143,081` |
| Margin above 1% threshold | about `35,150` bytes |

The compressed cmix payload inside the run was `108,929,925` bytes.

## Main Changes

One-line summary of the changes relative to `fx2-cmix`:

* `payload_lex`: reorders a structured PHDA9 tail region and appends compact EOF side data for exact restoration.
* `R1ORD3` side data: uses visible `D86a` fields plus Lehmer ranks to describe the reversible regime-1 order.
* `fxcm_v26` integration: ports Kaido Orav's stronger standalone text model into the cmix predictor stack.
* Updated article order: uses the article-order file included with the `fxcm_v26` archive.
* Disk-backed PPM improvements: keeps the PPM heap disk-backed while using `MADV_DONTNEED`, `MADV_RANDOM`, `O_NOATIME`, and `ftruncate`.
* Build/package updates: clang-17, PGO, and UPX 5.1.1.

More details are in [`changes.md`](changes.md).

## Platform

| Metric | Value |
| --- | --- |
| CPU | Intel Core i7-8700, 6 cores / 12 threads |
| RAM | 16 GB DDR4 |
| OS | Native Ubuntu run from a cmix binary built under WSL2 Ubuntu 18.04 |
| Storage | SATA SSD |
| Geekbench 5 `T` used for timing | `1200` |

## Run Measurements

Compression run:

| Metric | Value |
| --- | ---: |
| Wall time | `51:30:03` |
| User + system CPU time | `43:33:23` |
| Percent CPU | `84%` |
| User/system detail | `40:24:24` user + `3:08:58` system |
| Maximum resident set size | `9,696,008` KiB |
| Swap usage | `0` |
| Exit status | `0` |
| Estimated peak run-directory disk use | about `20.8` GB |

Verified full decompression run:

| Metric | Value |
| --- | ---: |
| Wall time | `54:31:14` |
| User + system CPU time | `43:04:55` |
| Percent CPU | `79%` |
| User/system detail | `39:58:02` user + `3:06:53` system |
| Maximum resident set size | `9,846,960` KiB |
| Swap usage | `0` |
| Exit status | `0` |

The decompressor produced a `1,000,000,000` byte `enwik9_uncompressed` file.
Its SHA256 matched the original `enwik9`:

```text
159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc  enwik9_uncompressed
159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc  enwik9
```

## Time Check

Must run below `70000/T` hours. With `T=1200`:

```text
70000/1200 = 58.33 h
43.56 h < 58.33 h
```

## Build

Install helper tools on Ubuntu if needed:

```bash
sudo apt update
sudo apt install build-essential libstdc++-14-dev
bash ./install_tools/install_upx.sh
bash ./install_tools/install_clang-17.sh
```

UPX `5.1.1` is required for building the final packed executable on newer
kernel versions. Older UPX versions can produce a packed binary that fails at
runtime, so the source package should be built with the provided UPX installer
or another confirmed UPX `5.1.1` binary.

Build the self-extracting compressor:

```bash
bash ./build_and_construct_comp.sh
```

The packaged compressor is written to:

```text
run/cmix
```

## Compress

Run from the `run` directory:

```bash
cd run
./cmix -e /path/to/enwik9 output.cmix
```

For accurate long-run timing, disable swap before running tests:

```bash
sudo swapoff -a
```

This avoids slowdowns from Linux/WSL swappiness during multi-day runs.

The self-extracting archive is written as:

```text
archive9
```

## Decompress

Run the archive from an empty or working directory:

```bash
chmod +x archive9
./archive9
```

The decompressor writes:

```text
enwik9_uncompressed
```

## Authors and Attribution

`cmix-lex` is derived from `fx2-cmix`, `fx-cmix`, cmix-hp, PAQ-family code, and
Kaido Orav's `fxcm_v26`.

Primary upstream authors include Kaido Orav, Byron Knoll, Matt Mahoney, and
other PAQ/cmix contributors.

cmix-lex-specific payload transform and integration work:

```text
Ibrahim Marcouch
```

## License

This project follows the GNU General Public License terms used by the upstream
cmix/fxcm/PAQ-family code. See [`LICENSE`](LICENSE).
