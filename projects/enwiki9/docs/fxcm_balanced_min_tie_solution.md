# Solution: FXCM Balanced-Minimum Tie Selection

## 1. Safety and priority

By definition, every member of `E` is unprotected and has the minimum priority
among unprotected slots. Since `h mod m` lies in `{0, ..., m-1}`,
`e[h mod m]` is a member of `E`. Therefore the selected slot is unprotected and
minimum-priority.

## 2. Balanced checksum counts

Apply Euclidean division:

```text
2^16 = q m + r
```

with `0 <= r < m`.

Among the integers from `0` through `2^16 - 1`, residues `0` through `r - 1`
occur `q + 1` times modulo `m`, and the remaining residues occur `q` times.
Therefore every tied slot is selected either:

```text
floor(2^16 / m)
```

or:

```text
ceil(2^16 / m)
```

times.

## 3. Imbalance

The only possible selection counts are `q` and `q + 1`, so the difference
between the largest and smallest count is at most one. This removes the
control's unconditional lowest-index preference while retaining a canonical
deterministic choice.

## 4. Algorithm

The first scan preserves the existing checksum-hit test. For eligible misses it
records the smallest priority and the number of slots attaining it. At least
`A - 2 >= 1` slots are eligible, so the tie count is positive.

Compute:

```text
pick = h mod tie_count.
```

The second scan visits eligible minimum-priority slots in increasing index
order and selects the slot at rank `pick`.

The algorithm uses `O(A)` time, two scans on a miss, one scan on a hit, and
`O(1)` additional storage.

## 5. Deterministic synchronization

Assume encoder and decoder states agree before an event. They therefore have
identical:

- checksums;
- protected indices;
- priorities;
- input checksum `h`;
- minimum tie set and tie count.

Both compute the same residue and select the same slot. They then apply the same
existing state update to the same slot and decoded bit. Their states agree
after the event. Induction over all events proves continued synchronization.

## Transfer boundary

The theorem proves deterministic balanced tie selection. It does not prove that
the changed replacement sequence improves codelength. Exact native roundtrip,
deterministic re-encode, archive bytes, package bytes, RSS, and runtime remain
authoritative.
