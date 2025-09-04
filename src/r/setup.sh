
#!/bin/bash
# A script to set up the Python environment for the Jetson LLM Engine.
# This version includes a post-build verification step to ensure GPU support.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
PYTHON_CMD="python3.10"
VENV_NAME=".venv"
BOLD=$(tput bold)
GREEN=$(tput setaf 2)
RED=$(tput setaf 1)
NC=$(tput sgr0) # No Color

# --- Script Start ---
echo "${BOLD}--- Starting Jetson LLM Engine Setup ---${NC}"

# 1. Check for critical system dependencies for GPU build
echo "Phase 1: Checking prerequisites..."
if ! command -v nvcc &> /dev/null; then
    echo "${RED}ERROR: NVIDIA CUDA Compiler (nvcc) not found in PATH.${NC}"
    echo "Please ensure the NVIDIA CUDA Toolkit is installed correctly and its 'bin' directory is in your PATH."
    exit 1
fi
echo "  [✔] Found 'nvcc'. CUDA Toolkit appears to be installed."

# 2. Check for Python
if ! command -v ${PYTHON_CMD} &> /dev/null; then
    echo "${RED}ERROR: Python command '${PYTHON_CMD}' not found.${NC}"
    exit 1
fi
echo "  [✔] Found Python command '${PYTHON_CMD}'."
echo "Phase 1 Complete."

# 3. Create or verify the virtual environment
echo -e "\nPhase 2: Setting up Python virtual environment..."
if [ -d "${VENV_NAME}" ]; then
    echo "  Virtual environment '${VENV_NAME}' already exists. Skipping creation."
else
    echo "  Creating virtual environment '${VENV_NAME}'..."
    ${PYTHON_CMD} -m venv ${VENV_NAME}
fi
echo "Phase 2 Complete."

# 4. Activate, upgrade pip, and install base requirements
echo -e "\nPhase 3: Installing dependencies..."
source "${VENV_NAME}/bin/activate"
pip install --upgrade pip > /dev/null 2>&1 # Hide noisy output
echo "  Upgraded pip. Now installing from requirements.txt..."
pip install -r requirements.txt > /dev/null 2>&1 # Hide noisy output
echo "Phase 3 Complete."

# 5. Build llama-cpp-python with CUDA support
echo -e "\n${BOLD}Phase 4: Building llama-cpp-python with GPU support...${NC}"
echo "This is the most critical step and may take a significant amount of time."
echo "Showing verbose build output:"
echo "--------------------------------------------------"
# The -v flag provides verbose output to monitor the build progress.
CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 pip install -v --upgrade --force-reinstall llama-cpp-python --no-cache-dir
echo "--------------------------------------------------"
echo "Phase 4 Complete."

# 6. Verify the build
echo -e "\n${BOLD}Phase 5: Verifying GPU support in the installed library...${NC}"
VERIFY_CMD="import llama_cpp; exit(0) if llama_cpp.llama_supports_gpu_offload() else exit(1)"
if python3 -c "$VERIFY_CMD"; then
    echo "${GREEN}  [✔] SUCCESS: The installed llama-cpp-python library reports that GPU offload is SUPPORTED.${NC}"
else
    echo "${RED}  [✖] FAILURE: The installed llama-cpp-python library reports that GPU offload is NOT SUPPORTED.${NC}"
    echo "${RED}    This means the model will run on the CPU, which will be extremely slow.${NC}"
    echo "${RED}    Please review the verbose build log above for errors related to 'nvcc', 'cuda', or 'cublas'.${NC}"
    exit 1
fi
echo "Phase 5 Complete."


echo "\n${BOLD}--- Setup Finished Successfully ---${NC}"
echo "To activate the environment in your terminal, run:"
echo "  ${GREEN}source ${VENV_NAME}/bin/activate${NC}"
echo "\nNext steps:"
echo "1. Download a model: ${BOLD}python scripts/download_model.py --repo-id ... --filename ...${NC}"
echo "2. Run the chat CLI: ${BOLD}python run_chat_cli.py --model your_model.gguf${NC}"
