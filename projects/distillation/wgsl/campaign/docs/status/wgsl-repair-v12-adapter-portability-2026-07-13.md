# WGSL Repair V12 Adapter Portability

The three external20 adapters are preserved at revision-pinned Git LFS URLs.
The reusable PEFT-to-Doppler bridge reproduces the frozen 628-token prompt,
validates adapter identity, and activates native PEFT LoRA matrix layouts. The
base and all three adapters now pass the unchanged V1 portability gate.

Matched layer-zero captures located the prior divergence in the split gated
SiLU operation. Doppler applied SiLU to both branches, computing
`SiLU(gate) * SiLU(up)`, while Qwen requires `SiLU(gate) * up`. Commit
`358653e7` corrects dense and MoE split callers and makes gated SiLU fail closed
unless the input-branch activation is explicit. The Qwen weights, tokenizer,
RDRR artifact, and LoRA adapter bytes were not changed.

The committed-code rerun produced exact deterministic completions and ten of
ten top-token overlap for the base and every adapter:

| Lane | Exact completion | Logit cosine | Delta cosine |
| --- | --- | ---: | ---: |
| Base | yes | 0.9997408 | n/a |
| Seed 11 | yes | 0.9998451 | 0.9996244 |
| Seed 29 | yes | 0.9998452 | 0.9995723 |
| Seed 47 | yes | 0.9997632 | 0.9996530 |

The failed attempts remain evidence. The float32 Transformers control rejected
reference precision as the cause, and the component capture then isolated the
runtime arithmetic defect. The passing receipt is bound to Doppler commit
`358653e78f0628c227b22edb32acfbd45220a67a` and has receipt hash
`629e4329923ab772ca050c4ad755794836b2d6a6612ed70af3b86d9fad09d9ab`.

No seed is selected because the frozen V1 policy has portability authority,
not checkpoint-selection authority. Semantic WGSL evaluation still lacks its
dispatch, CPU-oracle, numerical, metamorphic, bounds, and historical-regression
contract. WGSL Doctor remains unauthorized. The next step is a new frozen seed
selection policy on unexamined evidence, followed by the separately governed
semantic campaign.
