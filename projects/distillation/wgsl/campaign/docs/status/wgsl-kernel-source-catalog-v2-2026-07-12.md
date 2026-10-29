# WGSL ML Kernel Source Catalog V2

The V2 inventory records high-value WebGPU ML implementations without claiming
that every upstream is a ready-to-train WGSL corpus. The machine-readable
source of truth is
[wgsl-training-source-catalog-v2.json](../../tools/data/wgsl-training-source-catalog-v2.json),
SHA-256
`4b2a59317ccfd3819b37bd6b0a9a77c90b6f8e2839b2afcb89908e4e476672ed`.

| Source | Revision | License | Current role | Why |
| --- | --- | --- | --- | --- |
| Doppler | `90ca8e7d88e945f29a8f0c658a8c4f36d9cc6b26` | Apache-2.0 | training | Standalone inference, training, diffusion, and energy WGSL files compile under the declared verifier. |
| Zero-TVM | `32406c88acc201694df83a4e22df64bf4391d380` | MIT | external training | Standalone captured TVM shaders and handwritten browser-LLM kernels add out-of-domain structure. |
| MLC WebLLM | `21314560fe1e44f379c3415f1077362769ac5c94` | Apache-2.0 | reference | The runtime points to TVM-generated WebAssembly model libraries; the repository does not check in standalone materialized WGSL. |
| llama.cpp | `e3546c7948e3af463d0b401e6421d5a4c2faf565` | MIT | reference | Its WebGPU shader sources require preprocessing and specialization. |
| ONNX Runtime | `361184e61957410f19153754f325806972546d5b` | MIT | reference | WebGPU operator programs are emitted by TypeScript generators. |
| TensorFlow.js | `7f5309fef0a47545e34049903dbdae0f97285f7e` | Apache-2.0 | reference | Its WebGPU programs are TypeScript generators rather than standalone shader files. |
| CubeCL | `9110136fe5bb3c6e7dc0295100fe7f88342ceb6e` | Apache-2.0 | reference | The Rust compute compiler provides design diversity but needs a frozen lowering workload. |
| Apache TVM | `7356265096cba7196673b09f90b023e600171452` | Apache-2.0 | reference | The WebGPU code generator needs frozen models, shapes, schedules, and lowering receipts. |
| webgpu-llm | `e331fe1151540d688aa2fec9d18cec600356dd91` | MIT | quarantined | Its raw bundle destabilized source qualification and remains excluded pending isolated per-file receipts. |

`allowTraining` remains true only for Doppler and Zero-TVM. License
compatibility alone is not admission. A source must also have a pinned
materializer, exact specialization inputs, standalone shader text, clean
Radeon WebGPU compilation, and a reproducible mutation-repair receipt.

The V1 catalog remains byte-stable at
`ff99b6f2597f65be601cd48b668a1fae3d943de180eb3b4f7b95f50af4af161e`
because it is part of the V9 corpus lineage. Adding MLC WebLLM to V2 does not
rewrite the 2,714-row training corpus or imply that WebLLM code trained the
current Qwen adapter.

The next diversity work is to build one materializer at a time and compare it
with a random in-domain replacement control. Priority candidates are
ONNX Runtime and TensorFlow.js generator outputs, llama.cpp template
specializations, and a pinned MLC/TVM model build. Generated outputs enter a
new corpus version only after the same compile, provenance, license, family
split, and duplicate gates used by V1.
