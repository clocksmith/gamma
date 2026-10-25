# Public-domain foundation: six problems, both languages

A prospective, separately reviewed qualification of existing exact JavaScript and
Python sources against freely accessible official problem statements and explicit
local interface/effect policies. It does not reinterpret historical admitted
failures or compatibility probes, change old denominators, or qualify recognition.

## Observed result

All **12 source-language pairs** passed **3,844 checks in126 isolated executions**.
Independent host replay reproduced every verdict from hash-bound raw observations.

| Official problem ID | Cases per language | JavaScript | Python |
|---|---:|---|---|
|153|86|pass|pass|
|645|173|pass|pass|
|674|1,100|pass|pass|
|832|537|pass|pass|
|833|13|pass|pass|
|916|13|pass|pass|

The26 independently authored examples were supplemented by deterministic small
exhaustive and maximum-boundary cases, totaling1,922 per language. Expected outputs
stayed outside the sandbox. The original bwrap isolation and3CPU-second/8wall-second/
1GiB/4MiB per-call limits were unchanged; calls contained at most32cases.

Official clauses, all12 exact sources, independent oracle, local effects and153's
logarithmic interval reduction were reviewed before native execution. For832 the
local policy requires in-place matrix values and returned-root alias; it does not
claim original child-row identity. Other local effects require unchanged arguments
and no mutable input/result aliases.916 compares exact multiplicity with arbitrary
output order. These local policies are not misattributed to official statements.

Finite cases do not prove universal correctness or complexity. Only153 has an
explicit official logarithmic-time requirement; its static review is distinct
from runtime observations. Out-of-domain inputs are not admitted by these receipts.
No catalogue promotion or historical M1 achievement occurs automatically.

## Evidence identities

- Source/oracle/test/runtime freeze:
  `0c14de90535c23f1a7a05a94c5629ee4c3bc17bb5851bda298838819cc701b36`
- Independent pre-execution review:
  `063e1a140ea345182edaa54aed03dbacab850982fd5298a64615f874663683f1`
- Native execution report:
  `4229387cb12f3dc988ac206041fdfb577bf9f969f198701de11b2d1b42a7bf47`
- Independently replayed verifier receipt:
  `8f1993ef3751d20b7da8dd50dfb79f9d7e1caa8bdf5c6517c7cd1ba8796e563e`

Private source freezes and raw execution observations remain outside the
repository. The public official-clause summaries and independent example cases
are in `../domain-contracts-public-v1`. Protected final100/protected66 remained
closed.13focused infrastructure/oracle tests passed before the freeze.
