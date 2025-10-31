#!/bin/bash
# GAMMA launcher script with ROCm gfx1151 compatibility fix
#
# This script sets environment variables to make PyTorch work with gfx1151 GPUs
# by using gfx1100 as a compatible fallback architecture.

# Set HSA_OVERRIDE_GFX_VERSION to make gfx1151 act like gfx1100
# gfx1100 is supported by the PyTorch ROCm 6.1 wheel and is architecturally similar
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Disable problematic optimizations that may cause segfaults
export PYTORCH_HIP_ALLOC_CONF=expandable_segments:False
export PYTORCH_ROCM_ARCH=gfx1100

# Optional: Enable additional debugging if needed (uncomment to use)
# export AMD_SERIALIZE_KERNEL=3
# export TORCH_USE_HIP_DSA=1

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

# Run GAMMA with all passed arguments
python gamma.py "$@"
