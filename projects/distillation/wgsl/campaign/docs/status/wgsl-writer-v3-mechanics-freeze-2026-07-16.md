# WGSL Writer v3 mechanics freeze — 2026-07-16

## Decision

WGSL Writer v3 is a planned general-authoring campaign, not a trained writer and
not a product. Its response and evaluation mechanics are now explicit enough to
prevent a complete shader from being evaluated without the host program needed
to execute it. Corpus materialization, training, selection, promotion, and
productization remain blocked.

The target capability is:

> Complete executable WebGPU shader package from natural language and an
> explicit host contract.

## Frozen mechanics

- Campaign policy:
  `tools/policies/wgsl-writer-v3-campaign-policy.json`
  (`c98c18e26fe88464fb634d397bf8b52d07f12961e0ce9f8c0784abb053b604d5`)
- Model response schema:
  `src/config/schema/wgsl-author-package.schema.json`
  (`4766acc0b7528a687b322f8c882be28f12fc9e79604be32d04416cf4ea24a0b2`)
- Static package validator and prompt builder:
  `tools/lib/wgsl-author-package.js`
  (`bfd50832a936894d73122a41c3bc1d84ceab5f599b42fd20ed01ee5bcff5fca3`)
- Deterministic execution-plan resolver:
  `tools/lib/wgsl-author-execution-plan.js`
  (`970d5fa388725b9fc88453a3a515f93a88e1559da8797a96bccd6909463be08b`)
- Core copy-format catalog:
  `tools/data/wgsl-author-format-catalog.json`
  (`6c4849383eaba2c5c1f7e98ef6a53e8433294df4c90d62bc29bcb0773cdcd223`)
- Browser compute/render/multi-pass executor:
  `tools/lib/wgsl-author-browser-executor.js`
  (`86019ad15338c0b3bf2133680181e75d9906a4d2a3ca3d006e61b51357648948`)
- Frozen mechanics-reference manifest:
  `tools/data/wgsl-author-v3-reference/manifest.json`
  (`9fe9e2fc28ace5700226920cb2b0dc0c418ee524976817bfdff60d9a1334a55b`)
- Reference materializer, oracle library, and runner:
  `tools/lib/wgsl-author-reference.js`
  (`08006a28528eab0eed7cc6a56b572737766c5c4f3470d8ebd21b28568c7b4f20`)
  and `tools/run-wgsl-author-v3-reference.js`
  (`e807a426e62d5ca0846accaa590414e413b5de07d22cef5ed1a15fef9666de0a`)
- Capability-family plan:
  `tools/data/wgsl-writer-v3-capability-catalog.json`
  (`b78f4f08014f18ebbd08aeed1bbcb9d9b4be1d6758b151a2e875797341689258`)

One response now binds complete WGSL modules to declared device requirements,
host or generated resources, binding slots, compute dispatch expressions,
direct or indexed draws, render targets, pass order, and observable outputs.
The validator reconciles host-owned resources with the task contract and rejects
unknown features, unavailable limits, missing WGSL declarations, invalid entry
points, malformed expressions, unsupported resource use, and non-observable
outputs.

The planned development populations contain 20 family-disjoint capability
families: eight training, four calibration, four checkpoint-selection, and four
seed-confirmation families. Every role spans compute, render, and multi-pass
workloads. Compilation is only a prerequisite; actual execution, numerical or
raster oracles, bounds checks, metamorphic checks, variation, and historical
regressions are blocking.

## V2 relationship

The V2 seed-47 adapter may be compared as one initialization because its exact
Transformers-to-Doppler completion parity passed. Its evidence covers only
complete 1-D elementwise f32 compute shaders under explicit interfaces. No V2
capability claim transfers into V3. The selected adapter weights also lack an
immutable external URL and must be preserved before they can be relied on by a
new campaign.

## Blocking gaps

1. Qualify the new browser runner on reference compute, render, indexed-render,
   and multi-pass packages. The code allocates declared resources, compiles
   modules, executes passes, reads outputs, and emits an identity-bound receipt,
   but no WebGPU reference receipt exists yet.
2. Materialize licensed reference tasks with CPU numerical, CPU image, raster,
   cross-pass, bounds, metamorphic, and regression oracles.
3. Extend the response contract for depth/stencil, blending, indirect work, and
   query state, and qualify mipmapped and multisampled resource execution before
   those features enter a capability claim.
4. Qualify the reference packages, then freeze disjoint corpus rows and training
   workloads. Training is forbidden before this gate.
5. Preserve the V2 adapter artifacts and create a separately custodied, natural,
   family-disjoint, one-use promotion population.

## Verification

The following CPU-only contract checks pass:

```text
node tests/tooling/wgsl-author-package.test.js
node tests/training/wgsl-writer-v3-contract.test.js
node tools/check-policy-schema-registry.js
```

No browser/WebGPU execution was used for this freeze, so the implemented runner
remains unqualified.

## Claim boundary

This receipt proves a fail-closed response envelope, planned capability strata,
causal isolation, and gate order. It proves no V3 corpus, training, selected
checkpoint, semantic capability, general WGSL writer, or deployable authoring
product.
