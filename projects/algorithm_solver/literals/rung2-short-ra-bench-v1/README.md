# Matched Random-Access Size & Native-C Throughput Pareto Benchmark (`rung2-short-ra-bench-v1`)

Measures held-out archive bytes **and** native-C single-record random-access seek latency
(`ns/seek`) and throughput (`MiB/s`, `100,000` pseudo-random single-document seeks per cell)
across four matched `4 B/doc` random-access container codecs, kept strictly separate from
`../codenet-replication-v1/` and `dcc-v5`:

1. **`BIT3` (`ra_codecs_bench.c`):** Static `<= 16 B` dictionary + global canonical Huffman
   table(s) (`0` per-record block headers) + `4 B/doc` bit-offset seek index, decoded in C via a
   12-bit L1-resident canonical Huffman lookup table (`lut[4096]`) + overflow tree.
2. **`FSST-255` ([Boncz, Neumann, & Leis, *PVLDB* 13(11):2649–2661, 2020](https://doi.org/10.14778/3407790.3407851)):**
   Iterative 5-generation DP static symbol table (`<= 255` symbols of `1..8 B` + `0xFF` 2-byte
   escape) + `4 B/doc` byte-offset index, decoded in C via 8-byte unaligned word stores.
3. **`DFL3 (-15 + tuned zdict)`:** Raw headerless `DEFLATE` (RFC 1951 `wbits = -15`, zero magic,
   frame, or checksum bytes) with training-selected shared dictionary (`zstd --train` or raw corpus
   tail across `{0, 1, 2, 4, 8} KiB`) + `4 B/doc` byte-offset index, decoded in C via reused
   `zlib` `inflateReset` + `inflateSetDictionary`.
4. **`ZST3 (tuned --no-check)`:** `zstd -19 --no-check` with training-selected `maxdict` across
   `{0, 1, 2, 4, 8} KiB` + `4 B/doc` frame-offset index, decoded in C via reused `ZSTD_DCtx` +
   pre-digested `ZSTD_DDict`.

## Held-Out Size & Native-C Random-Access Speed Results (`results/ra_pareto_benchmark_v1.json`)

Every cell verifies 100% byte-for-byte reverse-order random-access decoding on all held-out files
before timing `100,000` pseudo-random single-record seeks:

| Held-Out Suite (`train -> test`) | Mean Doc | `BIT3` (`B` / `ns` / `MiB/s`) | `FSST-255` (`B` / `ns` / `MiB/s`) | `DFL3 (-15+zd)` (`B` / `ns` / `MiB/s`) | `ZST3 (DDict)` (`B` / `ns` / `MiB/s`) | 2D Pareto Frontier |
|---|---:|---|---|---|---|---|
| `codenet_held_out_K1024` (`400 -> 400`) | `677.5 B` | `98,725` / `1,635` / `396` | `160,982` / **`223`** / **`2,901`** | `94,637` / `1,181` / `548` | **`93,832`** / `683` / `947` | `['FSST-255', 'ZST3-tuned']` |
| `codenet_held_out_K4096` (`400 -> 400`) | `677.5 B` | `100,184` / `1,585` / `408` | `160,982` / **`232`** / **`2,789`** | `94,637` / `1,178` / `549` | **`93,832`** / `686` / `944` | `['FSST-255', 'ZST3-tuned']` |
| `short_wgsl_vs_json` (`160 -> 160`) | `149.0 B` | **`12,092`** / `227` / `627` | `14,618` / **`50.0`** / **`2,841`** | `12,842` / `513` / `277` | `14,678` / `195` / `731` | **`['BIT3', 'FSST-255']`** |
| `short_ts_vs_mjs` (`160 -> 160`) | `151.1 B` | **`12,390`** / `226` / `637` | `14,929` / **`52.7`** / **`2,732`** | `13,458` / `374` / `385` | `15,459` / `198` / `727` | **`['BIT3', 'FSST-255']`** |
| `med_ts_vs_json` (`100 -> 100`) | `587.6 B` | `30,109` / `889` / `631` | `37,646` / **`194`** / **`2,886`** | `27,664` / `1,387` / `404` | **`27,426`** / `750` / `747` | `['FSST-255', 'ZST3-tuned']` |
| `long_js_vs_wgsl` (`80 -> 80`) | `2,232.2 B` | `76,696` / `5,404` / `394` | `118,084` / **`761`** / **`2,799`** | `60,197` / `2,694` / `791` | **`59,935`** / `2,129` / `1,001` | `['FSST-255', 'ZST3-tuned']` |

## Key Findings

1. **2D Pareto Frontier Phase Transition at Short Record Lengths ($\bar{L}_{\text{doc}} \approx 150\text{ B}$):**
   - On medium and long records ($\bar{L}_{\text{doc}} \ge 588\text{ B}$), `{FSST-255, ZST3-tuned}`
     forms the 2D `(Archive Size, Seek Latency)` Pareto frontier (`ZST3` smallest via intra-file
     LZ77; `FSST-255` fastest at `2.8–2.9 GiB/s`).
   - On short random-access records ($\bar{L}_{\text{doc}} \approx 150\text{ B}$), **both `ZST3`
     and raw headerless `DFL3 (-15)` fall off the 2D Pareto frontier**:
     - `ZST3` (`14,678 B` and `15,459 B` @ `195–198 ns/seek`) is **strictly dominated by `FSST-255`**
       (`14,618 B` and `14,929 B` @ `50–53 ns/seek`) on **both** size and speed.
     - Raw headerless `DFL3 (-15 + zdict)` (`12,842 B` and `13,458 B` @ `374–513 ns/seek`) eliminates
       `zstd` frame headers via 3-bit RFC 1951 block headers, yet is **strictly dominated by `BIT3`**
       (`12,092 B` and `12,390 B` @ `226–227 ns/seek`, `627–637 MiB/s`) on **both** held-out size
       (`-5.8%` and `-7.9%` smaller) and random-access speed (`1.65–2.26x` faster, avoiding per-seek
       `inflateSetDictionary` window resets).
     - **`{BIT3, FSST-255}` is the unique 2D Pareto frontier at $\bar{L}_{\text{doc}} \approx 150\text{ B}$**,
       with `BIT3` saving **`17.0–17.3%` held-out archive bytes** relative to `FSST-255` (`17.6–19.9%`
       relative to `ZST3`) via variable-length canonical Huffman codes and `<= 16 B` phrases.
2. **CodeNet Held-Out Random-Access Throughput (DCC Venue Readiness):**
   - Native-C 12-bit LUT `BIT3` achieves **`395.8 MiB/s` (`1,635 ns/seek`)** at $K = 1{,}024$ and
     **`408.3 MiB/s` (`1,585 ns/seek`)** at $K = 4{,}096$ on held-out CodeNet (`primary -> secondary`),
     compared with `548–549 MiB/s` for raw `DEFLATE (-15 + zdict)`, `944–947 MiB/s` for pre-digested
     `ZSTD_DDict`, and `2,789–2,901 MiB/s` for `FSST-255`.

## Verification

```bash
/usr/bin/python3 -m py_compile fsst255_codec.py run_ra_pareto_bench.py test_ra_pareto_bench.py
/usr/bin/python3 -B test_ra_pareto_bench.py
```
