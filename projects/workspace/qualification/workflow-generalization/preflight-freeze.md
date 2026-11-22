# Step 1 Preflight and Freeze Record (`#88`)

Generated at **$0.00 spend** without rescoring `blind-holdout-v3` (`b4627512111e2662fdc7fcb767b3af6bd2859464`) or adding any synthetic suite.

## Environment & Pinned Revisions

- **Chrome revision:** `Google Chrome 158.0.8127.36`
- **Node runtime:** `v22.20.0`
- **Gamma frozen runtime commit:** `195be76ad1122dde984f35fe85bab070bde58ea1` (`gammaDirty: false`, `projects/workspace/src` tree `7d9bdfe3eff736c2b099427ee098059b4521146b`)
- **Fawn commit:** `a281360ff04321f08e5627c5309503d0259a0e70` (donor workspace import commit: `9234bc55953c43af7d53c7335d8fe24282e59dc6`)
- **Exact preflight command:** `node projects/workspace/qualification/workflow-generalization/preflight-freeze.mjs`
- **Preflight receipt:** [`receipts/preflight-freeze-receipt.json`](./receipts/preflight-freeze-receipt.json) — SHA-256 `a661c81b92f1e5ba1f8cb6547ecfe0630ae2dd898a10a4fda5640797108f1df2`

## Retained Receipt SHA-256 Ledger (Evidence Separation)

| Receipt | Classification | Pinned Commit | SHA-256 | Exact `$0` Replay Command |
| --- | --- | --- | --- | --- |
| [`receipts/blind-holdout-v3-receipt.json`](./receipts/blind-holdout-v3-receipt.json) | `frozen-single-pass-blind-score` | `b46275121` | `b7d4842a3446e3b5db40febdb242520155abec5e6ef8c04aa219ec4a7d5eda13` | `node projects/workspace/qualification/workflow-generalization/replay-verify-v3-receipt.mjs` |
| [`receipts/v3-independent-replay-verification.json`](./receipts/v3-independent-replay-verification.json) | `independent-detached-worktree-replay-verification` | `8f41cac9d` | `86c1f0f371e16fe667b5f094307a8c015d476121c7eb311dceb0309173a36712` | `node projects/workspace/qualification/workflow-generalization/replay-verify-v3-receipt.mjs` |
| [`receipts/post-v3-modular-revision-receipt.json`](./receipts/post-v3-modular-revision-receipt.json) | `post-v3-diagnostic-not-blind-score` | `34ae03d5b` | `cd3c0b9d83be06d506c258bdfb6abaebc5511ddbe01c3fe7bea29ade7a2239f3` | `node projects/workspace/qualification/workflow-generalization/modular-revision-eval.mjs` |
| [`receipts/host-contract-benchmark-receipt.json`](./receipts/host-contract-benchmark-receipt.json) | `contract-and-integration-cost-benchmark` | `0569aaa84` | `5a205cb87bd6c7982feef62353263f2d92b2c1aa1dd829d7c1a4116439f70e97` | `node projects/workspace/qualification/workflow-generalization/host-contract-benchmark.mjs` |

## Frozen `blind-holdout-v3` Integrity (`3/3` Files Verified Unchanged)

- `blind-holdout-v3/cases.mjs`: `fd15da2565673e34f5b2350f4fd793b593534a3d43da87af3b06ecfbc1908b8b` (`verified: true`)
- `blind-holdout-v3/PROTOCOL.md`: `653b4e218f58a1660763728de9f822e6edb1fec15df986afc1861b672f30a190` (`verified: true`)
- `blind-holdout-v3/self-check.mjs`: `f8c44de22695d6df5c39ea37d7dc8ef7ed4b7f7d9c182236069abb042190f2e2` (`verified: true`)
