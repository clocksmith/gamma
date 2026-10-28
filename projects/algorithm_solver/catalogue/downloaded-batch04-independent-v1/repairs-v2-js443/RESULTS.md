# Official named JS443 result

All four units passed under new freeze
`22a029248837d968ef79ab39a2e83db85226c8a570a05305cae0d1f95bf878ae`:
86 actual named `compress` calls, 86 class compatibility calls, 86 functional
`solve` calls, and 86 old v1 named alias negative-control calls. Every old named
alias call was rejected by the official integer-length/prefix contract.
All 344 requested observations completed across 12/12 complete interpreter
streams, with zero candidate errors. Jupiter and Mars raw replay are identical.

Selected JS source SHA256:
`788a7fadfbdf6295a82eafc88aa85db8a66e3b71517bf756fbaa0fbb6955c0ed`.
Only the standalone alias changed. Native effects, returned integer length and
prefix are checked; the unspecified tail is ignored. Constant workspace was
independently source reviewed. The old v1 source/freeze/raw/class proof remains
unchanged; its class proof is not official standalone JS execution proof.
Python v1 Solution.compress proof remains valid.

Raw archive SHA256:
`68df1c5ff98302294c5a9db0a053eff7bd13a1478e431116ed3cda083df74cce`.
Retention paths and source/runtime/adapter bindings are under `evidence/`.
No production service qualification or canonical promotion is implied.
