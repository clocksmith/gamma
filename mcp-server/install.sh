#!/bin/bash
# GAMMA MCP Server Installation Script

set -e

echo "============================================"
echo "GAMMA MCP Server Installation"
echo "============================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "server.py" ]; then
    echo "Error: Please run this script from the gamma/mcp-server directory"
    exit 1
fi

# Check if GAMMA venv exists
if [ -d "../venv" ]; then
    echo "✓ Found GAMMA virtual environment"
    source ../venv/bin/activate
else
    echo "⚠ Warning: GAMMA venv not found. Creating new virtual environment..."
    cd ..
    python3 -m venv venv
    source venv/bin/activate
    cd mcp-server
fi

# Install MCP SDK
echo ""
echo "Installing MCP SDK..."
pip install -q "mcp[cli]>=1.2.0"
echo "✓ MCP SDK installed"

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "from mcp.server.fastmcp import FastMCP; print('✓ FastMCP import successful')"

# Test server startup
echo ""
echo "Testing server startup (Ctrl+C to stop)..."
echo "If the server starts without errors, installation is complete!"
echo ""
echo "Press Ctrl+C after you see 'GAMMA MCP Server running'"
echo ""
sleep 2

timeout 5 python3 server.py || true

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Configure Claude Desktop - see README.md"
echo "2. Restart Claude Desktop"
echo "3. Look for GAMMA tools in Claude's tool menu"
echo ""
echo "Configuration file location:"
echo "  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "  Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo ""
echo "Add this to your config:"
echo '{'
echo '  "mcpServers": {'
echo '    "gamma": {'
echo '      "command": "python3",'
echo "      \"args\": [\"$(pwd)/server.py\"]"
echo '    }'
echo '  }'
echo '}'
echo ""
