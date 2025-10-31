#!/bin/bash
# Quick install script for gfx1151 PyTorch build
# Run this AFTER building PyTorch

set -e

echo "========================================="
echo "Installing PyTorch gfx1151 to venv"
echo "========================================="

# Activate venv
cd /home/clocksmith/deco/gamma
source .venv/bin/activate

echo "Current venv: $VIRTUAL_ENV"

# Go to PyTorch build directory
cd ~/pytorch-build/pytorch

echo ""
echo "Uninstalling old PyTorch from venv..."
pip uninstall -y torch torchvision torchaudio 2>/dev/null || true

# Go to PyTorch source directory
cd ~/pytorch-build/pytorch

# Initialize all submodules (critical!)
echo ""
echo "Initializing submodules (this may take 10-15 minutes)..."
git submodule sync
git submodule update --init --recursive

# Verify critical submodules exist
if [ ! -f "third_party/eigen/CMakeLists.txt" ]; then
    echo "❌ ERROR: eigen submodule failed to initialize"
    exit 1
fi

echo "✓ Submodules initialized"

echo ""
echo "Building wheel for gfx1151..."
export PYTORCH_ROCM_ARCH=gfx1151
export USE_ROCM=1
export ROCM_PATH=/opt/rocm-6.2.4
export CMAKE_PREFIX_PATH=${VIRTUAL_ENV}
export USE_CUDA=0
export BUILD_CAFFE2=0
export USE_DISTRIBUTED=0
export USE_NCCL=0  # Disable NCCL (NVIDIA-specific)
export USE_SYSTEM_LIBS=0  # Use bundled protobuf (will be patched below)
export BUILD_TEST=0  # Skip tests to save time
export MAX_JOBS=4
export CXXFLAGS="-Wno-error"  # Don't treat warnings as errors (needed for fbgemm)
export USE_FBGEMM=0  # Disable FBGEMM - BFloat16 kernels fail on gfx1151
# Let PyTorch auto-detect BLAS (will use rocBLAS for ROCm)

# Patch ALL third-party CMakeLists.txt files to fix CMake 3.5 compatibility
echo "Patching third-party CMakeLists.txt files for CMake 3.5 compatibility..."

# Comprehensive patch: Change ANY cmake_minimum_required version to 3.5.0
# Handles uppercase/lowercase, all old versions (1.x, 2.x, 3.0-3.4), with/without spaces
find third_party -name "CMakeLists.txt" -type f -exec sed -i -E \
  's/(cmake_minimum_required|CMAKE_MINIMUM_REQUIRED) *\(VERSION [0-9]+\.[0-9]+(\.[0-9]+)?/\1 (VERSION 3.5.0/g' {} \;

echo "✓ All CMakeLists.txt files patched to CMake 3.5.0"

# Disable -Werror in fbgemm (causes false positive warnings in AVX512 code)
echo "Disabling -Werror in fbgemm..."
sed -i 's/string(APPEND CMAKE_CXX_FLAGS " -Werror")/#string(APPEND CMAKE_CXX_FLAGS " -Werror") # Disabled/' \
  third_party/fbgemm/CMakeLists.txt
echo "✓ fbgemm -Werror disabled"

# Run AMD build script to hipify CUDA code for ROCm
echo "Running hipify script to convert CUDA code to HIP..."
python tools/amd_build/build_amd.py

# Clean any previous failed builds
echo "Cleaning previous build artifacts..."
python setup.py clean
rm -rf build dist

# Build wheel (this takes 1-2 hours)
echo ""
echo "⏳ Building PyTorch wheel (1-2 hours)..."
echo "   Monitor progress: tail -f /tmp/pytorch_build.log"
echo ""
python setup.py bdist_wheel 2>&1 | tee /tmp/pytorch_build.log

# Check if build succeeded
if [ ! -d "dist" ]; then
    echo "❌ ERROR: Build failed - no dist directory created"
    echo "Check log: /tmp/pytorch_build.log"
    exit 1
fi

# Install wheel
WHEEL=$(find dist -name "torch-*.whl" | head -1)
if [ -z "$WHEEL" ]; then
    echo "❌ ERROR: No wheel found in dist/"
    echo "Build may have failed. Check: /tmp/pytorch_build.log"
    exit 1
fi

echo ""
echo "✓ Build complete!"
echo "Installing wheel: $WHEEL"
pip install "$WHEEL"

# Verify installation
cd ~
echo ""
echo "Verifying installation..."
python -c "
import torch
print(f'✓ PyTorch {torch.__version__}')
print(f'✓ ROCm available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ GPU device: {torch.cuda.get_device_name(0)}')
    archs = torch.cuda.get_arch_list()
    print(f'✓ Supported architectures: {len(archs)} total')
    if 'gfx1151' in archs:
        print('  🎉 gfx1151 FOUND! GPU support enabled!')
    else:
        print(f'  ⚠️  gfx1151 not found. Available: {archs}')
else:
    print('✗ ROCm not available')
"

echo ""
echo "========================================="
echo "✅ Installation complete!"
echo "========================================="
echo ""
echo "Test with GAMMA:"
echo "  python gamma.py game --engine pytorch --model google/gemma-3-1b-it"
