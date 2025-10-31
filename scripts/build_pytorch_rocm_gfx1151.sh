#!/bin/bash
# Script to build PyTorch from source with ROCm support for gfx1151 GPU
# This will take 1-2 hours to complete

set -e  # Exit on error

echo "========================================="
echo "PyTorch ROCm gfx1151 Build Script"
echo "========================================="
echo ""
echo "This script will:"
echo "1. Install build dependencies"
echo "2. Clone PyTorch source code"
echo "3. Build PyTorch with gfx1151 support"
echo "4. Install into your virtual environment"
echo ""
echo "⚠️  WARNING: This will take 1-2 hours and requires ~20GB disk space"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Activate virtual environment (REQUIRED)
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    cd /home/clocksmith/deco/gamma
    source .venv/bin/activate
    cd -
fi

# Verify we're in venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "✓ Using virtual environment: $VIRTUAL_ENV"

# Check ROCm installation
if [ ! -d "/opt/rocm-6.2.4" ]; then
    echo "❌ ERROR: ROCm not found at /opt/rocm-6.2.4"
    echo "   Please install ROCm first: https://rocm.docs.amd.com/projects/install-on-linux/"
    exit 1
fi

echo "✓ ROCm found at /opt/rocm-6.2.4"

# Install build dependencies
echo ""
echo "Installing build dependencies..."
pip install cmake ninja pyyaml setuptools

# Create build directory
BUILD_DIR="$HOME/pytorch-build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clone PyTorch (if not already cloned)
if [ ! -d "pytorch" ]; then
    echo ""
    echo "Cloning PyTorch repository..."
    git clone --recursive https://github.com/pytorch/pytorch
    cd pytorch
    git checkout v2.6.0  # Match your current PyTorch version
else
    echo ""
    echo "PyTorch repository already exists, updating..."
    cd pytorch
    git fetch
    git checkout v2.6.0
    git submodule sync
    git submodule update --init --recursive
fi

# Set build environment variables
echo ""
echo "Configuring build for gfx1151..."
export PYTORCH_ROCM_ARCH=gfx1151
export USE_ROCM=1
export ROCM_PATH=/opt/rocm-6.2.4
export CMAKE_PREFIX_PATH=${VIRTUAL_ENV}
export USE_CUDA=0  # Disable CUDA
export BUILD_CAFFE2=0  # Skip Caffe2 to save time
export USE_DISTRIBUTED=0  # Skip distributed training to save time
export MAX_JOBS=4  # Limit parallel jobs to avoid OOM

# Clean previous build
echo ""
echo "Cleaning previous build artifacts..."
python setup.py clean

# Build and install into virtual environment
echo ""
echo "Building PyTorch (this will take 1-2 hours)..."
echo "Installing to: $VIRTUAL_ENV"
echo "You can monitor progress in another terminal with: tail -f /tmp/pytorch_build.log"
echo ""

# Uninstall old PyTorch first
pip uninstall -y torch

# Build wheel then install it
python setup.py bdist_wheel 2>&1 | tee /tmp/pytorch_build.log

# Find and install the wheel
WHEEL_FILE=$(find dist -name "torch-*.whl" | head -1)
if [ -z "$WHEEL_FILE" ]; then
    echo "❌ ERROR: No wheel file found in dist/"
    exit 1
fi

echo ""
echo "Installing wheel: $WHEEL_FILE"
pip install "$WHEEL_FILE"

# Verify installation
echo ""
echo "Verifying installation..."
cd ~
python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'ROCm available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

echo ""
echo "========================================="
echo "✅ PyTorch build complete!"
echo "========================================="
echo ""
echo "You can now use PyTorch with your gfx1151 GPU."
echo ""
echo "To test with GAMMA:"
echo "  python gamma.py game --engine pytorch --model google/gemma-3-1b-it"
