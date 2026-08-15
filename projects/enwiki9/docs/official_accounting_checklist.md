# Official Hutter Accounting Checklist

This checklist is for promoted `enwik9` candidates only. Prefix results,
forecasts, local proxy scores, and shadow-coder simulations do not satisfy this
checklist.

The canonical Gamma objective is
`contracts/research/v1/objective-contract.json`. This checklist expands its
prize-facing accounting procedure; conflicting prose does not override the
versioned contract.

## Score Object

The official-facing score must be audited as:

```text
S = length(comp9.exe or source package) + length(archive9.exe)
```

Local screening rows may use:

```text
S_local = program_proxy_bytes + archive_payload_bytes
```

`S_local` is useful for search. It is not a submission score.

## Active Local Budget

The current source-bound frontier is endpoint428 with a counted minified source
package of `261,125` bytes. Against the canonical target:

```text
target_score_bytes                         105,000,000
counted_minified_source_package_bytes          261,125
maximum_full_corpus_archive_payload_bytes  104,738,875
best_counted_forecast                      109,389,323
remaining_forecast_debt                      4,389,323
```

This is source-bound forecast accounting, not a full-corpus score. A child must
save at least `4,389,323 + added_program_bytes + added_framing_bytes` at full
scope relative to the forecast parent, with additional transfer safety before
full-1G authorization.

## `cmix-obias` Immediate-Candidate Ledger

The locally hash-bound external candidate uses the primary self-extracting
submission form. Its currently claimed counted files are:

| Role | Bytes | SHA-256 |
| --- | ---: | --- |
| self-extracting `archive9` | `108,009,834` | `664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900` |
| packaged compressor `cmix` | `459,989` | `eee69c879f4bbd58015efd4d34f55c6dc986ec818fa68c2f32a9ee5ab5568f68` |
| compressor head asset | `23,002` | `35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078` |

The head asset is required by compression and is therefore counted alongside
the compressor. A second physical copy is already embedded in `archive9` for
bare decompression. Both `cmix` and `archive9` identify as statically linked
x86-64 ELF files, and the archive starts successfully in an empty environment
from a unique directory. The claimed arithmetic is:

```text
S1 = 459,989 + 23,002 =      482,991
S2 =                         108,009,834
S  = S1 + S2 =               108,492,825
conservative full invocation =           48
conservative charged total =    108,492,873
published prize ceiling =    109,685,196
conservative ceiling margin =   1,192,323
Gamma target =               105,000,000
conservative target debt =      3,492,873
```

This is still zero-credit external accounting. The exact qualification ladder
is deliberately split so one success cannot inherit an unproved antecedent:

| Gate | Current evidence | Status |
| --- | --- | --- |
| first full-1G bare decode | job `20260809T220237Z_6e7fd20876`; live guard `results/cmix_obias_full1g_bare_decode_qm0_guard_v1.json` | running |
| second isolated full-1G decode | opening-1M sealed-filesystem preflight passed exactly under job `20260809T231106Z_cf04ecd339`; full scope waits for the first decode | authorized, not started |
| clean source build | q2 produced a `491,483`-byte program package, deterministic `464,298`-byte opening archives, and an exact bare inverse | opening qualification passed |
| clean build repeat identity | q3 reproduced q2's program, head, payload, and opening archive byte-for-byte | passed on current host/toolchain |
| full encode reproduction | isolated arms A/B each perform a full encode and exact bare inverse, followed by archive comparison | running |
| final submission accounting | exact submitted files, instructions, option bytes, source publication, runtime, RAM, and disk | incomplete |

The external source snapshot claims that `archive9` contains the matching
decode stub, compressed dictionary, head asset, payload, and framing. The
compressor still consumes the separately counted head through
`KH_BITLSTM32`. The exact operational line is
`KH_BITLSTM32=head.blob ./cmix -e enwik9 out.cmix`, which is `48` bytes without
a trailing newline; the self-extracting archive needs no option. The detailed
rules explicitly add necessary execution or compilation option lengths. The
ledger therefore carries the entire compressor invocation as a conservative
upper bound until the committee-facing package form fixes the exact surcharge.
Do not infer full encode reproducibility from a successful external-archive
decode or from an opening-prefix source roundtrip.

## External Rule Boundary

The Large Text Compression Benchmark and Hutter Prize rule sets are related but
not identical. Treat the Hutter Prize page as the prize authority, and use the
benchmark rules as an additional packaging sanity check.

Benchmark listing rules require the ranked size to include the compressed
`enwik9` size plus a decompressor archive containing any runtime files needed
by the decompressor, including dictionaries and configuration files. They also
require decompression without a network connection and without user-selected
options that change the restored contents.

Sources checked:

- Hutter Prize: `https://prize.hutter1.net/`
- Detailed Hutter rules: `https://prize.hutter1.net/hrules.htm`
- Large Text Compression Benchmark rules:
  `https://www.mattmahoney.net/dc/textrules.html`

## Counted Bytes

Count every byte required to reproduce the decompression result:

- compressor binary or source package submitted as `comp9`;
- self-extracting archive or archive payload submitted as `archive9`;
- wrapper scripts required to build, run, or select the candidate;
- command-line options that must be supplied if rules require them to be
  encoded or documented inside the package;
- bundled dictionaries, static tables, model weights, codebooks, manifests, and
  configuration files;
- local patches to external compressors if those patches are required;
- any reconstruction metadata that is not derivable from already-decoded bytes.

Do not count bytes that are derived deterministically by both encoder and
decoder from the already decoded stream, unless their generating code or tables
are shipped separately.

## Reproduction Requirements

A promoted result must provide:

- exact input corpus: `enwik9`, `1,000,000,000` bytes;
- exact restored byte count;
- hash of original input;
- hash of restored output;
- roundtrip status;
- deterministic replay status;
- archive hash when determinism compares physical archives;
- build command or source-package reconstruction command;
- run command;
- temporary-disk peak or bound;
- RSS peak under the selected guard;
- declaration that no GPU, network, hidden file, or uncounted dictionary was
  used.
- authoritative CPU/core/thread rule snapshot and adopted interpretation;
- allowed affinity, physical/logical CPU topology, OpenMP/runtime environment,
  and observed maximum live and runnable threads;
- reference benchmark version and score `T` plus independent compression and
  decompression wall times.

Endpoint428-specific runtime preflight is frozen in
`docs/endpoint428_cpu_thread_eligibility_contract.md`.

## Promoted Candidate Audit Sequence

For a candidate that passes full `1G` local replay, perform this audit before
writing any target-hit language:

1. Record the exact full-corpus driver result JSON and RSS guard JSON.
2. Verify `data_size == 1,000,000,000`, `roundtrip_ok == true`, and
   determinism is true in the same result artifact.
3. List every local proxy file and its byte size from the result's
   `program_files` field.
4. Build or identify the actual official `comp9` or source package artifact.
5. Build or identify the actual official `archive9` artifact.
6. Hash every counted package file and write the hashes into the promoted
   receipt.
7. Compute `official_score_bytes = comp9_or_source_package_bytes +
   archive9_bytes`.
8. Compute binary and decimal RSS margins from the recorded peak RSS.
9. Reject the target claim if official score, roundtrip, determinism, memory,
   hidden-input, network, or package-byte evidence is incomplete.

The local driver's `program_size` is evidence for the proxy package only. It
may equal, exceed, or undercount the official package depending on the final
submission shape. Treat equality as unproven until the official package bytes
are materialized and hashed.

## Memory Unit Risk

Historical cmix screens used:

```text
10 GiB = 10,485,760 KiB
```

Prize-facing gates now enforce:

```text
10 GB = 9,765,625 KiB
```

A candidate that merely passes the historical `10GiB` guard is not safe under
decimal `10GB`. Any promoted result should record both:

```text
binary_margin_kib = 10,485,760 - peak_rss_kib
decimal_margin_kib = 9,765,625 - peak_rss_kib
```

If `decimal_margin_kib < 0`, the result must be labeled as local-guard evidence,
not submission-grade memory evidence.

The fx2 prize runner enforces `max_sampled_tree_rss_kib` at `9,765,625` KiB.
This counts wrapper and child processes together. A promoted candidate still
needs a package-level audit of the exact submitted compressor/archive path.

## Promotion Receipt Template

```json
{
  "candidate": "",
  "scope_bytes": 1000000000,
  "archive9_bytes": null,
  "comp9_or_source_package_bytes": null,
  "official_score_bytes": null,
  "local_archive_payload_bytes": null,
  "local_program_proxy_bytes": null,
  "local_score_bytes": null,
  "roundtrip_ok": false,
  "determinism_ok": false,
  "sha256_original": null,
  "sha256_restored": null,
  "archive_sha256": null,
  "peak_rss_kib": null,
  "rss_guard_kib": 9765625,
  "rss_guard_limit_mode": "tree",
  "binary_margin_kib": null,
  "decimal_margin_kib": null,
  "temp_disk_bytes": null,
  "rule_snapshot_sha256": null,
  "rule_interpretation": null,
  "cpu_model": null,
  "allowed_cpu_affinity": [],
  "physical_cores_allowed": null,
  "logical_cpus_allowed": null,
  "max_live_threads_process_tree": null,
  "max_runnable_threads_process_tree": null,
  "openmp_environment": {},
  "reference_benchmark": null,
  "reference_score_t": null,
  "compress_wall_seconds": null,
  "decompress_wall_seconds": null,
  "gpu_used": false,
  "network_used": false,
  "hidden_inputs": false,
  "counted_files": []
}
```

## Claim Rule

Do not write that a candidate hits `10.5000000%` unless:

```text
scope_bytes == 1,000,000,000
roundtrip_ok == true
official_score_bytes <= 105,000,000
```
