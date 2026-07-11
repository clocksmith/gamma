# AMD enwiki9 Migration Receipt

Generated from live host, toolchain, filesystem, SSH, and corpus probes.

- Generated at UTC: `2026-07-11T21:56:02.888723+00:00`
- Ready: `false`
- Proof boundary: `infrastructure receipt only; no compression score claim`

## Blockers

- `destination_filesystem_not_ready`
- `amd_host_user_or_destination_unset`
- `corpus_waiting_for_source_manifest`
- `proof_search_layout_not_prepared`
- `non_proof_checkout_not_prepared_or_labeled`

## Host

- Hostname: `128`
- User: `x`
- Python executable: `/usr/bin/python3`
- Python version: `3.14.4 (main, Jun 18 2026, 14:25:02) [GCC 15.2.0]`

### `lscpu -e`

```text
CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE    MAXMHZ   MINMHZ       MHZ
  0    0      0    0 0:0:0:0          yes 5187.5000 625.0000 1770.4890
  1    0      0    1 1:1:1:0          yes 5187.5000 625.0000 3543.4390
  2    0      0    2 2:2:2:0          yes 5187.5000 625.0000 3542.3210
  3    0      0    3 3:3:3:0          yes 5187.5000 625.0000 1769.5970
  4    0      0    4 4:4:4:0          yes 5187.5000 625.0000 3557.7759
  5    0      0    5 5:5:5:0          yes 5187.5000 625.0000 2000.0000
  6    0      0    6 6:6:6:0          yes 5187.5000 625.0000 3539.6350
  7    0      0    7 7:7:7:0          yes 5187.5000 625.0000 3547.2471
  8    0      0    8 8:8:8:1          yes 5187.5000 625.0000 2000.0000
  9    0      0    9 9:9:9:1          yes 5187.5000 625.0000 2009.8650
 10    0      0   10 10:10:10:1       yes 5187.5000 625.0000 2008.5710
 11    0      0   11 11:11:11:1       yes 5187.5000 625.0000 2000.0000
 12    0      0   12 12:12:12:1       yes 5187.5000 625.0000 2010.9440
 13    0      0   13 13:13:13:1       yes 5187.5000 625.0000 1749.8370
 14    0      0   14 14:14:14:1       yes 5187.5000 625.0000 1749.2830
 15    0      0   15 15:15:15:1       yes 5187.5000 625.0000 1998.7209
 16    0      0    0 0:0:0:0          yes 5187.5000 625.0000 2000.0000
 17    0      0    1 1:1:1:0          yes 5187.5000 625.0000 3536.1560
 18    0      0    2 2:2:2:0          yes 5187.5000 625.0000 3547.2759
 19    0      0    3 3:3:3:0          yes 5187.5000 625.0000 2000.0000
 20    0      0    4 4:4:4:0          yes 5187.5000 625.0000 2000.0000
 21    0      0    5 5:5:5:0          yes 5187.5000 625.0000 2000.0000
 22    0      0    6 6:6:6:0          yes 5187.5000 625.0000 2000.0000
 23    0      0    7 7:7:7:0          yes 5187.5000 625.0000 2000.0000
 24    0      0    8 8:8:8:1          yes 5187.5000 625.0000 1898.9160
 25    0      0    9 9:9:9:1          yes 5187.5000 625.0000 2012.8970
 26    0      0   10 10:10:10:1       yes 5187.5000 625.0000 1992.6340
 27    0      0   11 11:11:11:1       yes 5187.5000 625.0000 2001.1689
 28    0      0   12 12:12:12:1       yes 5187.5000 625.0000 1753.2111
 29    0      0   13 13:13:13:1       yes 5187.5000 625.0000 1748.5360
 30    0      0   14 14:14:14:1       yes 5187.5000 625.0000 2000.0000
 31    0      0   15 15:15:15:1       yes 5187.5000 625.0000 2000.0000
```

### RAM

```text
               total        used        free      shared  buff/cache   available
Mem:     131891228672  3521777664 125693702144    39251968  4431376384 128369451008
Swap:     8589930496  3692302336  4897628160
```

### Kernel

```text
Linux 128 7.0.0-22-generic #22-Ubuntu SMP PREEMPT_DYNAMIC Mon May 25 15:54:34 UTC 2026 x86_64 GNU/Linux
```

### Compiler

```text
g++ (Ubuntu 15.2.0-16ubuntu1) 15.2.0
Copyright (C) 2025 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

## Tooling

- All requested commands present: `true`

| Command | Present | Path | Version |
|---|---|---|---|
| `git` | `true` | `/usr/bin/git` | `git version 2.53.0` |
| `rsync` | `true` | `/usr/bin/rsync` | `rsync  version 3.4.1  protocol version 32` |
| `g++` | `true` | `/usr/bin/g++` | `g++ (Ubuntu 15.2.0-16ubuntu1) 15.2.0` |
| `make` | `true` | `/usr/bin/make` | `GNU Make 4.4.1` |
| `python3` | `true` | `/usr/bin/python3` | `Python 3.14.4` |
| `pip3` | `true` | `/usr/bin/pip3` | `pip 25.1.1 from /usr/lib/python3/dist-packages/pip (python 3.14)` |
| `gzip` | `true` | `/usr/bin/gzip` | `gzip 1.14` |
| `xz` | `true` | `/usr/bin/xz` | `xz (XZ Utils) 5.8.3` |
| `sha256sum` | `true` | `/usr/bin/sha256sum` | `sha256sum (uutils coreutils) 0.8.0` |
| `md5sum` | `true` | `/usr/bin/md5sum` | `md5sum (uutils coreutils) 0.8.0` |
| `b2sum` | `true` | `/usr/bin/b2sum` | `b2sum (uutils coreutils) 0.8.0` |
| `cksum` | `true` | `/usr/bin/cksum` | `cksum (uutils coreutils) 0.8.0` |
| `unzip` | `true` | `/usr/bin/unzip` | `UnZip 6.00 of 20 April 2009, by Debian. Original by Info-ZIP.` |
| `ssh` | `true` | `/usr/bin/ssh` | `OpenSSH_10.2p1 Ubuntu-2ubuntu3.2, OpenSSL 3.5.5 27 Jan 2026` |

## Filesystems

```text
Filesystem                        Type      1B-blocks          Used   Available Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4  1964601909248 1832611069952 32119009280  99% /
/dev/mapper/ubuntu--vg-ubuntu--lv ext4  1964601909248 1832611069952 32119009280  99% /
tmpfs                             tmpfs   65945616384    2559135744 63386480640   4% /tmp
/dev/mapper/ubuntu--vg-ubuntu--lv ext4  1964601909248 1832611069952 32119009280  99% /
```

### Storage basis

- Current working tree `du -sb`: `807786884804	/home/x/deco/gamma`
- Current enwiki9 subtree `du -sb`: `252696637	/home/x/deco/gamma/projects/enwiki9`
- Current tracked files: `6398631637	total`
- The 128 GiB gate budgets a clean checkout plus two working trees, corpus
  and source archive, mmap traces, compressor scratch, build/archive/receipt
  space, and a free reserve. It does not budget a byte-for-byte copy of the
  current working tree's unrelated generated project artifacts.

## Destination

- Configured: `false`
- Path: `unset`
- Minimum free bytes: `137438953472`
- Ready: `false`
- Reason: `AMD_DEST is unset and --destination was not supplied`

Required layout:

- `proof_checkout`: `<AMD_DEST>/checkouts/gamma-proof`
- `non_proof_checkout`: `<AMD_DEST>/checkouts/gamma-non-proof`
- `non_proof_label`: `<AMD_DEST>/checkouts/NON_PROOF_RESEARCH_ONLY.md`
- `portable_proof_build`: `<AMD_DEST>/build/portable-proof`
- `native_search_build`: `<AMD_DEST>/build/native-search`
- `incoming_corpus`: `<AMD_DEST>/data/incoming-unaccepted`
- `canonical_corpus`: `<AMD_DEST>/data/canonical`
- `mmap_scratch`: `<AMD_DEST>/scratch/mmap`
- `compressor_scratch`: `<AMD_DEST>/scratch/compressor`
- `archives`: `<AMD_DEST>/archives`
- `receipts`: `<AMD_DEST>/receipts`

## SSH

- AMD_HOST: `unset`
- AMD_USER: `unset`
- Destination: `unset`
- Identity configured: `false`
- Authorized keys bytes on this host: `0`
- Verified: `false`

## Proof Artifact Migration

- Fingerprint audit OK: `true`
- Fingerprint status counts: `{"match": 285}`
- Candidate audit OK: `true`

## Corpus Quarantine

- Quarantine: `unset`
- Manifest status: `pending_source_manifest`
- Accepted: `false`
- Canonical promotion allowed: `false`

| File | Bytes | MD5 | SHA256 | BLAKE2b |
|---|---:|---|---|---|
| `enwik9.zip` | n/a | n/a | n/a | n/a |
| `enwik9` | n/a | n/a | n/a | n/a |

## Next Commands

Do not run these with placeholders. Supply the intended values first.

```bash
export AMD_HOST=<host-or-tailnet-name>
export AMD_USER=<remote-user>
export AMD_DEST=<dedicated-mounted-path>
ssh -o BatchMode=yes "${AMD_USER}@${AMD_HOST}" 'id -un; hostname; pwd'
python3 projects/enwiki9/tools/enwiki9_migration_receipt.py \
  --amd-host "$AMD_HOST" --amd-user "$AMD_USER" \
  --destination "$AMD_DEST" --probe-ssh \
  --quarantine <independent-quarantine> \
  --source-manifest <source-manifest.json>
```

The corpus remains unaccepted until the supplied source manifest matches
both file sizes and SHA256 values. A manifest MD5, when present, must also
match. The receipt tool never promotes quarantine files automatically.
