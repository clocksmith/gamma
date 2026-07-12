# Dependency Profiles

`requirements.txt` remains the stable CPU-oriented installation entrypoint. The
files in this directory contain shared, engine-specific, and hardware-specific
profiles.

```bash
# Default CPU-compatible environment
pip install -r requirements.txt

# Shared dependencies without a compute runtime
pip install -r requirements/base.txt

# Hardware profiles
pip install -r requirements/cuda.txt
pip install -r requirements/rocm.txt

# Engine extras
pip install -r requirements/pytorch.txt
pip install -r requirements/llamacpp.txt

# Verifier-guided SFT, DPO, and GRPO after installing hardware torch
pip install -r requirements/verifier-training.txt
```

Available profiles are `base`, `core`, `cuda`, `jax`, `llamacpp`, `mlx`,
`onnx`, `pytorch`, `rocm`, `tensorflow`, `verifier-training`, and `vllm`.
