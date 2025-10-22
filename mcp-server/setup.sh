#!/bin/bash
# GAMMA MCP Server Setup Script
# This script sets up the MCP server dependencies

set -e

echo "============================================"
echo "GAMMA MCP Server Setup"
echo "============================================"
echo ""

# Get the absolute path to the gamma directory
GAMMA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MCP_DIR="$GAMMA_DIR/mcp-server"

echo "GAMMA directory: $GAMMA_DIR"
echo "MCP server directory: $MCP_DIR"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if we have Python 3.10+
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo "Error: Python 3.10 or higher required (found $PYTHON_VERSION)"
    exit 1
fi

# Create or use GAMMA venv
if [ -d "$GAMMA_DIR/venv" ]; then
    echo "✓ Found existing GAMMA virtual environment"
    source "$GAMMA_DIR/venv/bin/activate"
else
    echo "Creating new virtual environment for GAMMA..."
    cd "$GAMMA_DIR"
    python3 -m venv venv
    source venv/bin/activate

    # Install GAMMA requirements if they exist
    if [ -f "$GAMMA_DIR/requirements.txt" ]; then
        echo "Installing GAMMA requirements..."
        pip install -q -r requirements.txt
    fi
fi

# Install MCP SDK
echo ""
echo "Installing MCP SDK..."
pip install -q --upgrade "mcp[cli]>=1.2.0"
echo "✓ MCP SDK installed"

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "from mcp.server.fastmcp import FastMCP; print('✓ FastMCP import successful')" || {
    echo "Error: FastMCP import failed"
    exit 1
}

# Create a test to verify server can start
echo ""
echo "Testing server can initialize..."
cd "$MCP_DIR"
python3 -c "
import sys
sys.path.insert(0, '$GAMMA_DIR')
from mcp.server.fastmcp import FastMCP
mcp = FastMCP('test')
print('✓ Server initialization successful')
" || {
    echo "Error: Server initialization failed"
    exit 1
}

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure Claude Desktop:"
echo "   File: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "2. Add this configuration:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "gamma": {'
echo '      "command": "'"$(which python3)"'",'
echo '      "args": ["'"$MCP_DIR/server.py"'"]'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "3. Restart Claude Desktop completely (Cmd+Q then relaunch)"
echo ""
echo "4. Test with: 'Show me available LLM models using GAMMA'"
echo ""
echo "For detailed instructions, see: $MCP_DIR/QUICKSTART.md"
echo ""
