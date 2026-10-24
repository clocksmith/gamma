# Item49: public preflight analytical null

2026-10-24. The proposed fixed-multiplier support-budget certificate cannot
produce a positive lower bound at **any** budget k. This follows from public
item35 metadata; no private sources, q arrays, dictionaries, cases or validation
were read, and no support-budget trajectory or experiment was run.

The [design and proof](DRAFT.md) validly restrict at most256 paid dictionary
entries to at most k entries occurring in exactly one distinct fit source.
Singletons and unused paid entries count. It keeps35's full allowed substring
universe and fixed300 source populations. The bound is
`ceil((L(q) - T_k(q))/D)`, where `T_k(q) >= 0` is the exact largest activation
charge subject to the support budget. At k256 it equals35's unrestricted bound.

However, the recorded-best35 multipliers already have **negative path terms**:

| Fixed300 cohort | Recorded numerator | Top256 charge | L = numerator + charge | Ceiling of L / D |
|---|---:|---:|---:|---:|
| R | −27,266,973,950 | 12,435,442,807 | −14,831,531,143 | −14,831 |
| naming | −28,259,230,310 | 11,798,958,032 | −16,460,272,278 | −16,460 |

D is1000000. These final-column values are **upper bounds on the proposed
certificate values for every k**, not new lower bounds on F, and not measured
k0 values. Subtracting a nonnegative activation charge cannot make them positive.
The second proposed point, q0, gives the unchanged negative bounds −37980 and
−37943 at every k. Taking the better of these two q points therefore still cannot
exclude ten-percent character fraction for any k.

[public_audit.py](public_audit.py) reads only the public35 evidence and verifies
the path-sum identity against all300 public integer path numerators, the accepted
independent-replay flags, denominators and integer ceilings. Its retained
[public-preflight.json](public-preflight.json) binds that evidence by SHA256.
This arithmetic audit relies on35's prior independent replay; it is not a fresh
replay of private q or sources. [REVIEW.md](REVIEW.md) independently checks the
proof and the public authority chain.

Five small invented-source tests passed with the pinned Python runtime:

```
/home/x/deco/gamma/.venv_rocm/bin/python -m unittest -v test_prototype.py
```

They cover exhaustive activation/weak-duality comparisons, support classification,
singletons/bans, compressed multiplicities, ties, empty classes, fewer entries,
bin boundaries, zero q, k256 equality, and corrupted public arithmetic. No
synthetic complexity benchmark or production runner was built or run. There is
no execution contract, activation, optimization, witness, or qualification.

The **support-budget concept remains untested under support-optimized q**. Such
an optimizer could change L as well as the activation penalty; this analytical
null says nothing about its best achievable bound. It also provides no semantic
reuse finding, positive feasibility witness, M1 exclusion, or conclusion for
other populations, source choices or representations. Component intent and all
existing acceptance gates remain unchanged.
