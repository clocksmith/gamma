# cmix-obias algorithmic geometry-order substitution Qm0

Status: frozen pre-execution plan; external-parent archive screen; zero score
credit

Candidate:

```text
cmix_obias_geometry_order_substitution_qm0_v1
```

## Question

Can the exact public `cmix-obias` predictor gain at least `5,000` archive
bytes on canonical opening 10M when its fixed article order is replaced by the
already source-bound Gamma geometry key, while retaining a path that deletes
the donor's `199,671`-byte compressed order asset?

This is an order-only backend transfer. It does not transplant `obias`, the
bit residual head, LSTM width, arithmetic coding, PPM memory policy, or runtime
changes into endpoint428. The public parent remains an unverified external
self-report and receives zero Gamma score credit.

## Why this gate is target-bearing

The public donor reports:

```text
full archive9                         108,009,834 bytes
packaged compressor                      459,989 bytes
separate bit-head blob                     23,002 bytes
reported counted total                108,492,825 bytes
fixed comp_order inside compressor        199,671 bytes
```

An algorithmic order with a frozen `32,768`-byte implementation allowance
would reduce the program side by at most:

```text
199,671 - 32,768 = 166,903 bytes
```

before archive effects. The resulting no-archive-gain envelope is
`108,325,922`, leaving `325,922` bytes to the standing `108,000,000` target.
An exact `5,000`-byte opening-10M archive gain projects to `500,000` bytes at
1G and therefore leaves a provisional `174,078`-byte cushion:

```text
108,492,825 - 166,903 - 500,000 = 107,825,922
```

That projection is only a gate threshold. It is not a forecast, score claim,
or transfer certificate.

The choice of 10M is deliberate. On the different FX2 backend, the frozen
geometry transform improved the archive by only `80` bytes at 1M, `5,603`
bytes at 10M, and `107,386` bytes at 100M. An opening-1M scientific kill would
therefore be poorly matched to the known scale behavior.

## Bound parent and inputs

External repository:

```text
URL       https://huggingface.co/dfreelan/cmix-obias
commit    51488a0c1228dbeab7c1be837fc90ceaed351728
```

As-built assets:

```text
packaged cmix
  bytes       459,989
  SHA-256     eee69c879f4bbd58015efd4d34f55c6dc986ec818fa68c2f32a9ee5ab5568f68

raw executable prefix
  bytes       159,704
  SHA-256     24f52d24e5ff5027fa76ea75864a76b7d627917f75df14c64091f1f37b519ec0

compressed dictionary
  bytes       100,598
  SHA-256     353caf87f6ea9b3a66b1691c6777ee04b24f0c9b5a1c9c3212652597521ca6f8

compressed public order
  bytes       199,671
  SHA-256     ebb9015438c52ba5d75276792235994a0e5af5e5ca31f2ed437d19259e0eae37

raw public order
  bytes       1,094,862
  SHA-256     eecd462c29319bab185b48229c4d09ab52f16ca9c582e8e32eff9a7c2a7de39e

bit-head blob
  bytes       23,002
  SHA-256     35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078
```

Corpus:

```text
full enwik9 bytes       1,000,000,000
full SHA-256            159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc
Qm0 prefix bytes           10,000,000
Qm0 SHA-256             5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97
```

The donor documents the exact opening-10M parent values:

```text
payload       1,599,218 bytes
archive9      1,882,538 bytes
```

Qm0 must reproduce both sizes rather than importing them as measured Gamma
evidence.

## Frozen order definitions

All order files contain donor-compatible non-redirect ordinals. Redirects are
recognized by the exact public five-prefix test and remain in the donor's
ordinary unused-page tail. Ties are resolved by numeric page ID and then
original physical page ordinal.

`B0` is the exact public fixed order.

`T0` sorts non-redirect pages by the normalized exact title:

```text
lowercase ASCII
replace each maximal non-[a-z0-9] run with one space
trim
truncate to 240 bytes
```

`G0` uses the frozen Gamma geometry key:

```text
if one or more [[Category:...]] fields exist:
    normalize("c " + sorted(raw categories) + " t " + title[:40])
else if an {{Infobox...}} name exists:
    normalize("i " + infobox name)
else:
    normalize("x " + first template name, or title when absent)
```

The regexes, case folding, truncation, and tie rules are copied exactly from
`fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`. There is no category width,
title width, template grammar, redirect placement, or key-family sweep.

## Exact execution

For every realized arm:

1. Verify the donor commit and every bound asset.
2. Materialize the exact opening-10M prefix.
3. Construct the arm's raw order twice and require byte identity.
4. Compress the order with the exact raw donor executable.
5. Build `cmix = raw executable + comp_dict + comp_order + 16-byte header`.
6. Encode with the exact fp16 head blob.
7. Preserve the actual payload and `archive9` sizes and SHA-256 hashes.
8. Bare-decode `archive9` without external assets.
9. Require byte-identical reconstruction of the opening-10M input.
10. Record maximum single-process and aggregate process-tree RSS.

Execution order is intentionally conditional:

```text
B0 public parent
G0 geometry substitution

if and only if B0 - G0 >= 5,000 archive bytes:
    T0 title-only control
    second clean G0 encode
```

The conditional order saves computation on a decisive miss. It cannot create
a pass because the promotion inequality is frozen before either result is
read.

## Accounting

Primary Qm0 archive gain:

```text
G_archive_10m = bytes(B0 archive9) - bytes(G0 archive9)
```

Diagnostic fixed-table program size:

```text
P_arm_fixed = 159,704 + 100,598 + bytes(comp_order_arm) + 16 + 23,002
```

Frozen algorithmic program ceiling:

```text
P_G0_algorithmic <= 159,704 + 100,598 + 16 + 23,002 + 32,768
                 <= 316,088 bytes
```

The final two numbers are planning ceilings only. A passing source-level
child must build and count its actual executable or reconstructive source
package.

## Decision

`AUTHORIZE_SOURCE_CHILD` requires all of:

```text
donor commit and asset identities                    exact
B0 payload size                                      1,599,218
B0 archive9 size                                     1,882,538
B0 bare roundtrip                                    exact
G0 raw-order rebuild                                 byte-identical
G0 bare roundtrip                                    exact
G0 archive gain over B0                              >= 5,000 bytes
G0 archive size                                      < T0 archive size
second clean G0 payload and archive                   byte-identical
all observed probabilities/coder executions          valid
```

A pass authorizes only one source-level child that replaces the order file
with the exact `G0` generator, followed by exact 10M package accounting and
one frozen distant-10M replay. It does not authorize a forecast change, 100M,
1G, or a claim that the external parent satisfies the memory/runtime rules.

If `G0` gains fewer than `5,000` bytes, the tool returns a scientific
`REJECT` after B0 and G0 and does not run T0 or the repeated encode. If G0
passes the gross gate but loses to T0 or is nondeterministic, it also rejects.
A valid rejection exits zero.

Retire on a scientific miss:

```text
this exact donor backend
this exact non-redirect event universe
this exact geometry key
this exact fixed-order substitution
the 32,768-byte algorithmic-source envelope
```

Do not sweep key widths, category limits, redirect placement, title tie-breaks,
order-codec settings, PGO profile, LSTM width, head weights, `obias` strength,
or PPM memory settings. Infrastructure or provenance failures receive no
scientific verdict and return nonzero.

## Evidence boundary

Qm0 is an external-parent experiment. Even a pass receives zero score credit
until the parent and child are source-bound, the actual package is counted,
chronological/distant transfer is measured, decimal-10GB and one-core runtime
are qualified, and a full-1G exact replay exists.
