# WIKI-PDA v2 q1-v3 authority review

Status: frozen, dormant, zero credit

The original WIKI-PDA v2 execution plan is stale because it binds the revoked
q1 policy-v4/v2-verifier path. The correction-only execution successor is
`wiki_pda_structural_replay_ceiling_q0_v2_execution_v2.json`.

The successor preserves the scientific candidate exactly:

- candidate ID: `wiki_pda_structural_replay_ceiling_q0_v2`
- candidate tree SHA-256:
  `8f674767ceb8f452f24f2167460f89519957652624340ef3ecdcd1dfa2302419`
- scanner SHA-256:
  `3e9aebfa0b32aa57fc23eb41b91bfc6dde737ff0428fbe28a7fa1ac52af4b82f`
- transformed population: `587,138,826` bytes, SHA-256
  `7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce`
- required D correct-byte ceiling: `4,079,243`
- controls: unchanged D/R/S/N opportunity matching and chronological-thirds
  predicates
- resource ceilings: unchanged `65,536 KiB` tree/VmHWM,
  `256,000,000` cgroup bytes, `100,000,000` scratch bytes, one logical CPU

Only the parent-authority axis changes. The new runner requires a future active
q1 policy revision 7 or later, a schema-valid q1-v3 receipt, a byte-exact stored
q1-v3 verification, a fresh independent rerun of the v3 verifier, and an empty
managed full-1G namespace. The decision binds both the active authority policy
and the dormant v6 design policy. The independent WIKI-PDA verifier rederives
the frozen scientific decision and the new authority chain.

Static acceptance completed: both Python files parse as ASTs; both new schemas
are valid Draft 2020-12 schemas; the execution plan validates; all 32 plan
bindings reopen with exact hashes; the scanner and candidate tree hashes equal
their predecessor values; and `git diff --check` passes. No scanner, corpus
hash, compiler, compressor, cgroup, or result writer was executed. The live qm8
lease remains untouched.

This correction grants no archive, compression, score, or Hutter objective
credit. Execution remains unauthorized until the q1-v3 authority artifact
exists and the exclusive namespace is released.
