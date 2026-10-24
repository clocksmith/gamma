# Potential lift: proof and invented complexity measurement

[Premeasurement design](DRAFT.md), [review](REVIEW.md),
[fixed synthetic specification](synthetic-spec.json),
[measured receipt](synthetic-results.json),
[proposed next adapter](DRAFT-NEXT.md).

The potential construction preserves an old occurrence certificate's path value
while adding every allowed exact substring. Under exact source, ban and pool
identity, its k=0 bound is at least the old bound when k limits the number of
paid entries occurring in exactly one source. This offers a different
certificate from [item 49's uninformative fixed q points](../support-budget-certificate-v1/README.md).
No corpus lift has been executed and no new Gamma exclusion is claimed here.

For old backward integer distances d and denominator D, retain every old q
exactly. A new occurrence i->j receives
`qnew=max(0,d_i-d_j-D*b)`, where b is 9 for a singleton and −1 otherwise. Every
path costs at least d_0 by telescoping, and an old tight path still achieves
d_0. Shared strings were already in item 28, so their weights are unchanged.
Exact top256 charges with at most k one-owner entries yield valid lower bounds
on F=10C−N for every k=0,...,256. All paid entries, including singletons, count.
This is an aggregate fraction relaxation, not a canonical or package optimum.

One predeclared invented measurement completed in **20.589 seconds**, including
both optimized constructions, separate all-depth replays, and 17 small oracle
tests. Peak RSS was 489,168KiB on core 6, under the 180-second/8GiB envelope. Every
one of the257 rows agreed independently for each fixture; no second run occurred.

| Invented fixture | Programs / characters | Old pool / occurrences | Full allowed entries | Old replay + index | New charge aggregation | Independent replay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Paired65-character prefixes | 300 / 75,000 | 313,344 / 758,605 | 8,966,636 | 3.539s | 0.348s | 11.310s |
| Repeated one-owner periods | 12 / 12,000 | 101 / 12,832 | 143,070 | 0.175s | 1.123s | 1.814s |

Pool construction and q generation are additional measured phases in the
receipt; the table does not sum to whole-job time. The paired fixture used
75,019 unique-entry range-minimum queries and only 6 repeated new-occurrence
contributions. The periodic stress used 5,991,440 repeated contributions. The
independent checker streamed all 9,109,706 allowed depths across both fixtures,
checked 771,437 old edge inequalities and 87,000 tight suffix positions, and
reconstructed all 514 allocation rows. It shares the accepted item 33 suffix
index/completeness verifier but uses separate occurrence enumeration, path
relaxation, support classification, weight enumeration and top selection.

The arbitrary, predeclared synthetic q was not optimized. Its paired-fixture
k0/k256 bounds were −714,965/−839,437; periodic bounds were 84,146/−116,365,267.
These values are mechanism checks, not research-corpus findings. The positive
periodic k0 value coexists with a negative unrestricted endpoint, illustrating
why the conditional and full-class claims must remain distinct.

The old Gamma item 28 bounds 22,196/13,725 would be retained or strengthened at k0
**only after exact private identity and certificate replay**. That replay has
not happened. Small-k infeasibility may reflect unique characters rather than
semantic reuse; larger k is not proved sufficient. A negative lifted bound
does not bound the optimal dual value from above. Near-whole entries, one-owner
entries and semantic reuse remain unresolved M1 issues; no witness, action
gain,400/500-population result, qualification or promotion follows.

The optimized representation avoids quadratic new-string storage. Repeated
one-owner aggregation still has a quadratic worst case; independent replay
streams all depths. These invented sizes do not establish a corpus ETA or a
universal runtime guarantee. Production and reporting remain separately proposed
in [DRAFT-NEXT](DRAFT-NEXT.md), with no binder or launch authorized by this record.
No private source, q, pool, validation input or case was read for this work.

Specification SHA256:
`066ea7e7c9a092643e5c5791d671cdb872e4e9b6ce088b503d7534044bc42cd0`.
Receipt SHA256:
`bceb5b672ec730041b8e650b298e6991b847dda9123a9399aaafd77ff0ec6fec`.
The eight measured code/document pins remain unchanged. Component intent and
production boundaries are preserved; this is supplied-input mathematical and
synthetic feasibility evidence only.
