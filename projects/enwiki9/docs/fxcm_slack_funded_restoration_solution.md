# Solution: Slack-Funded Capacity Restoration

Replacing every baseline record saves `a-b` bytes, hence releases

```text
R=(a-b)N.
```

Restoring `M` records at the compact width costs

```text
C=bM.
```

All other payload terms are unchanged, so subtraction gives the exact net
difference:

```text
Delta=C-R=bM-(a-b)N.
```

If `Delta<=0`, the restored construction is payload-nonincreasing. If
`Delta>0`, any certified headroom `H>=Delta` covers the increase by direct
addition. This proves only the stated resource model; it does not identify
payload with resident memory.

A canonical verifier computes `R`, `C`, and `Delta`, checks both component
equalities, and checks the final payload identity.

## Frozen result

```text
released by SLC:
  4 * 27,955,200 = 111,820,800 bytes

idx13 restoration:
  92 * 2,097,152 = 192,937,984 bytes

net declared increase:
  192,937,984 - 111,820,800 = 81,117,184 bytes
```

The restored total ContextMap2 capacity is 30,052,352 cells and its compact
payload is 2,764,816,384 bytes. This receives zero resource and score credit
until native gates pass.
