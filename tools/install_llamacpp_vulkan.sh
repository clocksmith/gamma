#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Missing ${VENV_PYTHON}. Create the virtualenv first."
  exit 1
fi

if ! command -v vulkaninfo >/dev/null 2>&1; then
  echo "vulkaninfo not found. Install Vulkan userspace tools first."
  echo "Example (Ubuntu): sudo apt install -y vulkan-tools mesa-vulkan-drivers"
  exit 1
fi

echo "Verifying Vulkan runtime..."
vulkaninfo >/dev/null

echo "Rebuilding llama-cpp-python with Vulkan backend..."
"${VENV_PYTHON}" -m pip uninstall -y llama-cpp-python >/dev/null 2>&1 || true
CMAKE_ARGS="-DGGML_VULKAN=ON" \
  "${VENV_PYTHON}" -m pip install --no-binary llama-cpp-python llama-cpp-python

echo "Checking llama.cpp GPU offload support..."
"${VENV_PYTHON}" - <<'PY'
from llama_cpp import llama_supports_gpu_offload
print(f"llama_supports_gpu_offload={llama_supports_gpu_offload()}")
PY

echo "Done. Use llamacpp with GPU offload:"
echo "  python gamma.py game --engine llamacpp --model /path/to/model.gguf --llama-cpp-n-gpu-layers -1"
