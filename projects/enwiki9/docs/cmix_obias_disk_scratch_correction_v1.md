# CMIX Disk-Scratch Correction

## Evidence requiring correction

The active source-built Arm B uses a working directory under `/dev/shm`, whose
filesystem is `tmpfs`. A live snapshot found 13,416,424 KiB allocated in that
directory, 8,468,088 KiB anonymous process PSS, and 1,159,472 KiB mapped shmem.
Mapped shmem is part of the tmpfs allocation and is not added twice. Process RSS
alone therefore cannot establish the prize memory boundary. Arm B remains useful
for terminal roundtrip and A/B identity evidence but is resource-noncompliant.

The sealed PPM0 policy is probability-neutral in intent, but dropping mappings
does not turn tmpfs backing into disk. Running PPM0 on `/dev/shm` would not prove
the required memory boundary.

## Correction-only successor

The disk runner layer forces all inherited source/build/encode/decode temporary
directories, Python temporary streams, and child `TMPDIR` onto the receipt-bound
root selected by `GAMMA_ENWIK9_DISK_SCRATCH`, defaulting to
`/home/x/enwiki9-scratch`. Before any build it parses `/proc/self/mountinfo` and
rejects `tmpfs` and `ramfs`. The result receipt binds the resolved root, mount
point, source, filesystem, mount options, and pre-run available bytes.

This changes no corpus byte, source revision, compression parameter, model,
probability, archive contract, package boundary, or score. It has zero Gamma
compression credit. The correction must prove:

```text
disk-backed scratch filesystem
allocated scratch <= 100,000,000,000 bytes
process-tree RSS <= 9,765,625 KiB
exact payload identity against the matched clean control
exact bare decode and canonical inverse
complete scratch-before and scratch-after-cleanup receipts
```

The first authorized diagnostic after Arm B audit is
`cmix_obias_ppm_always_purge_250k_disk_q0_v2`. The midpoint v3 algorithm is
replayed only through the separately versioned disk runner
`cmix_obias_bithead_delta_midas512_disk_q0_v5`; the sealed v3 overlay is not
mutated.
