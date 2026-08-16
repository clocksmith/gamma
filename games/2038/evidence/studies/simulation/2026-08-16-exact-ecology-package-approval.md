# Exact-ecology package approval

Date: 2026-08-16
Evidence label: approved strategy-catalog promotion
Verdict: exact-ecology strategy profile package approved as the canonical automated ecology

## Approval

The user approved this exact record:

> **Approve the exact-ecology strategy package recorded in
> `2026-08-15-exact-ecology-package-precision-confirmation-v1.md` for canonical
> strategy-catalog promotion. Freeze all non-strategy-catalog rule and content
> values until user approves a separately scoped human evidence cycle.**

## Package artifacts

- **Profiles promoted:**
  - `infrastructure_compounder`
  - `trust_governor`
  - `agi_candidate`
  - `power_broker`
- **Profile source proposals:**
  - [`proposals/exact-ecology-infrastructure-candidate-v1.json`](proposals/exact-ecology-infrastructure-candidate-v1.json)
  - [`proposals/full-ecology-agi-candidate-v1.json`](proposals/full-ecology-agi-candidate-v1.json)
  - [`proposals/capacity-operator-v1.json`](proposals/capacity-operator-v1.json)
  - [`2026-08-15-current-trust-evolution-v1.raw.json`](2026-08-15-current-trust-evolution-v1.raw.json)
- **Profile SHA-256 chain:**
  - `exact-ecology-infrastructure-candidate-v1.json`: `af0cefe1680c20469430dc94cfa78572ac6150d1e9e7234708a468e6872e3566`
  - `full-ecology-agi-candidate-v1.json`: `3bca97e398eab032ae5befe322f266f67b21119ed68848f2cc2f4661016c94a6`
  - `capacity-operator-v1.json`: `186bb26d4eaf01fedbb03bb3e7e0ad89a4aa6e544dcf6737142be70a7672b6f7`
  - `current-trust-evolution-v1.raw.json`: `a2a26d027b06d85c75178e6c6c468aa6ad3c5ae32b82292e3d84caeca173a462`

## Evidence chain

- **Holdout confirmation:**
  - [`2026-08-15-exact-ecology-package-holdout-v1.md`](2026-08-15-exact-ecology-package-holdout-v1.md)
  - Raw report: `2026-08-15-exact-ecology-package-holdout-v1.raw.json`
  - Archive: `20260816T081043781Z-unified-matrix-audit-0-14-7-03ac2fbdec61-mandate-2038-exact-ecology-package-holdout-v1-11998x4-unified-matrix-cli.json`
  - Raw/archive SHA-256: `0d190f300265ecc0ce48c29ffe6a362daa45eeef5f7c3d4d04f2b2be5a7faf01`
- **Precision confirmation:**
  - [`2026-08-15-exact-ecology-package-precision-confirmation-v1.md`](2026-08-15-exact-ecology-package-precision-confirmation-v1.md)
  - Raw report: `2026-08-15-exact-ecology-package-precision-confirmation-v1.raw.json`
  - Archive: `20260816T085423771Z-unified-matrix-audit-0-14-7-03ac2fbdec61-mandate-2038-exact-ecology-package-precision-confirmation-v1-25510x4-unified-matrix-cli.json`
  - Raw/archive SHA-256: `e07d51ca114784a4cbdc375ded22b6f412f19fa78771ca4ec82620e15169ba20`
- **Preregistrations:**
  - `preregistrations/exact-ecology-package-holdout-v1.json`
  - `preregistrations/exact-ecology-package-precision-confirmation-v1.json`
- **Source commit at approval write:** `686b6ed9eebe37ed415d527e67ac8f603054ff5b`
- **Source state:** clean? `false` (content strategy JSON still pending commit)

## Strategy-catalog update

The following canonical file is updated under this approval:

- `content/runtime/player-strategies.json`

No changes were made to rulebook copy, faction text, component lists, core
action semantics, scoring formulas, board topology, card pools, physical-kit
specifications, or browser UI flow.

## Surface audit

- Canonical strategy catalog (`content/runtime/player-strategies.json`):
  approved profiles now active.
- Dist strategy catalog (`dist/runtime/player-strategies.json`): matches generated
  strategy source.
- Simulator, browser prototype, and simulation study command surface: unchanged
  engine and schema identity.
- Rulebook and physical components: unchanged.
- Current validation status:
  - All 256 test cases (`npm test`) pass with the exact-ecology package promotion in place.
  - Project contract, provenance lint, boundary checks, content graph compilation, and release artifact verification (`npm run check`) pass cleanly.

## Decision boundary

- Approved content is **strategy-catalog and profile-identity scoped only**.
- This does not certify full game balance, human negotiation quality, duration,
  learnability, or fun.
- Physical rulebook and all non-strategy numeric surfaces remain frozen at
  existing identities until separately approved.
- Human/physical evidence is still required for product-level promotion.
