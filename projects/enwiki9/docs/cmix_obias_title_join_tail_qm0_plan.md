# cmix-obias Side-Free Title-Join Tail Qm0

Status: frozen zero-credit external-parent representation screen

Candidate: `cmix_obias_title_join_tail_qm0_v1`

## Question

Can the `payload_lex` regime-1 metadata blocks be placed in a compression-
useful order and restored without the transmitted `R1ORD3` permutation?

The decoder has already reconstructed the complete post-WRT stream before the
PHDA9 inverse. The main portion contains every page body and exact page title.
The tail contains one metadata block per complete page. A title-join codec can
therefore sort the metadata blocks by the exact associated title, then attach
the sorted blocks to the body slots obtained by sorting those already decoded
titles by the same bytewise order. No per-occurrence permutation is sent.

This is not a retry of the retired unchanged `payload_lex` transfer. That
experiment retained the public payload-key sort and paid a `679,489`-byte raw
side permutation. Qm0 changes the reversible representation by replacing the
side permutation with a decoder-visible exact join key.

## Frozen evidence and parent

The construction uses the retained, receipt-bound full-corpus artifacts from
`cmix_lex_payload_transfer_v1_retry2`:

```text
original_ready.bin       586,459,321 bytes
SHA-256                   cb466004e5d76000ba7d44a1a4a47245c203f4e8fbb62ffca7799692c966ff4f

transformed_ready.bin    587,138,826 bytes
SHA-256                   7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce

R1ORD3 side                  679,489 bytes
SHA-256                   98bae9de75b13b0a4f66f33cd24f1c45b145237eb4f99b363c9cb4e6ef918d95

public encoded side contribution 346,948 bytes
```

The scoring model is the exact `cmix-obias` raw executable and head at donor
commit `51488a0c1228dbeab7c1be837fc90ceaed351728`:

```text
raw executable           159,704 bytes
SHA-256                   24f52d24e5ff5027fa76ea75864a76b7d627917f75df14c64091f1f37b519ec0

head                       23,002 bytes
SHA-256                   35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078
```

This external parent receives no Gamma forecast credit.

## Exact association proof

Parse the exact public `.main_reordered` page stream and the untransformed
regime-1 metadata blocks. Require:

```text
complete pages                     243,425
metadata blocks                    243,425
exact titles unique                243,425
missing title or revision ID       0
block/page revision-ID mismatch    0
```

The first `D86a` integer in metadata block `i` must equal the first revision
ID in reordered page `i`. This binds every block to exactly one page before
any title order is evaluated.

## Arms

All arms contain the same regime-1 bytes and omit the public side blob during
the slice comparison.

```text
O0  original metadata-block order
P0  public payload-key block order
T0  exact associated-title byte order
TR  titles rotated forward by 37 page positions before ordering
```

`TR` is reversible and decoder-visible: the decoder obtains the page-title
vector from the reconstructed body sequence, applies the same fixed rotation,
and sorts by the resulting keys. It preserves the title distribution and
capacity while destroying the correct block/title association.

For P0, independently rebuild the public payload-key order from the original
blocks and require byte identity with the retained transformed regime. For T0
and TR, independently undo the order and require byte identity with O0.

## Exact reset-state screen

Use the same three 250,000-byte regime-1 slices as the earlier public transfer
gate: start, midpoint, and end. Compress and decode every O0, P0, T0, and TR
slice with the exact cmix-obias executable in no-preprocess mode and the exact
head. Require exact restored bytes and the strict decimal-10GB memory guard.

The first T0 pass authorizes a repeated T0 encode only if all economic and
control gates pass. The repeat must be byte-identical.

## Economics and decision

The public full score is external evidence only:

```text
cmix-obias reported total          108,492,825
standing target                    108,000,000
external-parent debt                   492,825
public encoded side contribution      346,948
maximum frozen order-asset ceiling     166,903
joint optimistic ceiling               513,851
```

The order-asset ceiling is not an achieved saving and is not added to any
score. It only explains why preserving P0-level tail economics while removing
the side is target-bearing enough to justify a native successor.

Authorize one paid full-state source child only when all conditions hold:

```text
all bound artifact hashes                     exact
page/block revision alignment                 exact
titles unique                                 exact
P0 rebuilt regime identity                    exact
T0 and TR inverse                             exact
all slice arithmetic decodes                  exact
all memory guards                             pass
T0 aggregate bytes                            <= P0 aggregate bytes
T0 no worse than O0                           on every slice
T0 aggregate bytes                            < TR aggregate bytes
conditional T0 repeat                         byte-identical
```

A pass authorizes only a source-level implementation and one exact native
full-state accounting gate. It does not authorize forecast movement, 100M, or
1G compression.

A miss retires this exact title join, bytewise title order, 37-position
specificity control, regime, and reset-state screen. Do not sweep title
normalization, rotations, hash widths, slice positions, or block boundaries.
A materially different body-derived join key requires a new lower-bound
certificate.
