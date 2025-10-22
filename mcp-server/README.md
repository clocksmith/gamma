# GAMMA MCP Server

Model Context Protocol server that exposes [GAMMA](../README.md)'s comprehensive LLM experimentation toolkit through standardized MCP primitives.

## Overview

GAMMA MCP Server transforms GAMMA's powerful local LLM capabilities into an MCP-compatible service, enabling LLM applications like Claude Desktop to:

- **Discover Models**: List all available models from Ollama, HuggingFace, and local GGUF files
- **Run Inference**: Execute single-shot generation with performance metrics
- **Compare Models**: Side-by-side analysis of different models on identical prompts
- **Benchmark Performance**: Comprehensive throughput and latency testing
- **Smart Selection**: AI-powered model recommendations based on task and constraints

## Architecture

The server exposes three MCP primitive types:

### Resources (Read-Only Data)

- `gamma://models/available` - Lists all detected models with hardware requirements
- `gamma://engines/status` - Inference engine capabilities and compatibility
- `gamma://benchmarks/{model_id}` - Historical benchmark data for specific models

### Tools (Executable Functions)

- **`run_inference`** - Execute prompt with specified model/engine
- **`compare_models`** - Run identical prompt across multiple models
- **`benchmark_model`** - Comprehensive performance testing
- **`select_optimal_model`** - Intelligent model recommendation

### Prompts (Guided Workflows)

- **`model_selection_wizard`** - Interactive model selection assistant
- **`comparison_setup`** - Structured multi-model comparison workflow

## Installation

### Prerequisites

- Python 3.10 or higher
- GAMMA installed and working (see [parent README](../README.md))
- At least one model available (Ollama, HuggingFace, or local GGUF)

### Setup

From the `gamma/mcp-server` directory:

```bash
# Install MCP SDK and dependencies
pip install "mcp[cli]>=1.2.0"

# Verify GAMMA is accessible
cd ..
python gamma.py --help

# Test the MCP server
cd mcp-server
python server.py
```

The server should start without errors. Press Ctrl+C to stop.

## Claude Desktop Integration

### Configuration

Add the GAMMA MCP server to your Claude Desktop configuration:

**File location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "gamma": {
      "command": "python",
      "args": [
        "/ABSOLUTE/PATH/TO/deco/gamma/mcp-server/server.py"
      ]
    }
  }
}
```

**Important:** Replace `/ABSOLUTE/PATH/TO/deco` with your actual path. Get this by running:
```bash
cd /Users/xyz/deco/gamma/mcp-server
pwd
```

### Restart Claude Desktop

After saving the configuration, completely quit and restart Claude Desktop for changes to take effect.

### Verification

In Claude Desktop, look for the hammer/tools icon. You should see GAMMA tools listed:

- ✅ `run_inference`
- ✅ `compare_models`
- ✅ `benchmark_model`
- ✅ `select_optimal_model`

## Usage Examples

### Example 1: Discover Available Models

```
Show me what models are available on my system
```

Claude will use the `gamma://models/available` resource to list all detected models.

### Example 2: Run Inference

```
Use the GAMMA server to generate a Python function that calculates
factorial using the smallest available model
```

Claude will:
1. Check available models
2. Select appropriate model
3. Use `run_inference` tool to generate code
4. Return results with performance metrics

### Example 3: Compare Models

```
Compare gemma-2-2b-it and qwen2-1.5b-instruct on the prompt
"Explain recursion in one sentence"
```

Claude will use `compare_models` to run both models and show side-by-side results.

### Example 4: Benchmark a Model

```
Benchmark the performance of qwen3-coder:30b with 5 iterations
```

Claude will use `benchmark_model` to test throughput and latency.

### Example 5: Smart Model Selection

```
I need a model for code generation with maximum 16GB VRAM,
prioritizing quality over speed. What should I use?
```

Claude will use `select_optimal_model` to analyze constraints and recommend the best option.

## How It Works

### Request Flow

1. **User asks question** in Claude Desktop
2. **Claude analyzes** available tools and resources
3. **Claude decides** which GAMMA tools to invoke
4. **MCP server executes** tool via GAMMA's engine infrastructure
5. **Results returned** to Claude with performance metadata
6. **Claude formulates** natural language response
7. **User sees** final answer with GAMMA insights

### Under the Hood

The server wraps GAMMA's existing components:

- **Model Discovery** → `src/game/model_discovery.py`
- **Engine Management** → `src/engines/`
- **Hardware Detection** → `src/utils/hardware.py`
- **Inference** → `src/game/model_handler.py`

All MCP communication uses stdio transport with JSON-RPC 2.0 messages.

## Advanced Usage

### Using Specific Engines

```
Run inference using llama.cpp engine on qwen3-coder with
temperature 0.9 and top-k 50
```

All GAMMA parameters (temperature, top-k, top-p, max_tokens) are exposed through the `run_inference` tool.

### Guided Workflows

Use GAMMA prompts for structured assistance:

```
Start the model selection wizard to help me choose a model
```

Claude will activate the `model_selection_wizard` prompt template and guide you through the decision process.

## Troubleshooting

### Server Not Appearing in Claude Desktop

1. **Check configuration path** - Ensure absolute path is correct
2. **Verify Python** - Make sure `python` command works: `which python`
3. **Check logs** - Look in Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
4. **Test manually** - Run `python server.py` to check for errors
5. **Restart** - Fully quit and restart Claude Desktop

### "No models available" Error

1. **Install Ollama** - Download from [ollama.com](https://ollama.com)
2. **Pull a model** - Run `ollama pull gemma2:2b`
3. **Verify in GAMMA** - Test with `python gamma.py game`

### Import Errors

Make sure you're running the server from the correct virtual environment:

```bash
cd /Users/xyz/deco/gamma
source venv/bin/activate  # Activate GAMMA's venv
cd mcp-server
python server.py
```

### Performance Issues

- **First run slowness** - Model loading takes time, especially for large models
- **VRAM errors** - Use smaller models or quantized versions
- **Timeout** - Increase max_tokens or use faster engine (llama.cpp)

## Development

### Project Structure

```
mcp-server/
├── server.py           # Main MCP server implementation
├── __init__.py         # Package initialization
├── pyproject.toml      # Python project configuration
└── README.md           # This file
```

### Key Components

**Resources:**
- Auto-discover models from multiple sources
- Detect hardware capabilities
- Track benchmark history

**Tools:**
- Wrap GAMMA's inference engines
- Handle async execution
- Return structured results with metadata

**Prompts:**
- Provide guided workflows
- Template complex interactions
- Improve user experience

### Extending the Server

To add new tools:

```python
@mcp.tool()
async def my_new_tool(param: str) -> str:
    """Tool description for Claude.

    Args:
        param: Parameter description

    Returns result description.
    """
    # Your implementation
    return result
```

FastMCP automatically generates tool schemas from type hints and docstrings.

## Security Considerations

### Safe by Design

- **No external network** - All operations are local
- **Read-only resources** - Model lists don't modify system
- **Sandboxed execution** - GAMMA runs in controlled environment
- **User confirmation** - Claude Desktop shows tool calls before execution

### Best Practices

1. **Review prompts** - Check what Claude wants to execute
2. **Monitor resources** - Large models can consume significant VRAM/RAM
3. **Validate inputs** - Server validates all parameters
4. **Check logs** - Server logs to stderr for debugging

## Performance

### Typical Latency

- **Model discovery** - 1-3 seconds (cached after first call)
- **Small models (2B)** - 0.5-2 seconds per inference
- **Large models (30B)** - 5-15 seconds per inference
- **Benchmarking** - 10-60 seconds depending on iterations

### Optimization Tips

1. **Use llama.cpp** - Fastest engine for GGUF models
2. **Enable GPU** - Dramatically faster than CPU inference
3. **Quantized models** - 4-bit/8-bit models save VRAM
4. **Batch operations** - Compare multiple models in one request

## Technical Details

### Protocol Version

- **MCP Version**: 2025-03-26
- **SDK**: `mcp[cli]>=1.2.0`
- **Transport**: stdio (JSON-RPC 2.0)

### Dependencies

- **Required**: `mcp[cli]`, Python 3.10+
- **GAMMA**: All GAMMA dependencies (PyTorch, transformers, etc.)
- **Optional**: llama-cpp-python, vllm, mlx (for specific engines)

### Logging

All logs go to **stderr** (not stdout) to comply with stdio transport requirements:

```python
logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stderr)]
)
```

Never use `print()` in the server code - it corrupts JSON-RPC messages.

## Related Documentation

- [GAMMA Main README](../README.md) - Core GAMMA documentation
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Protocol details
- [Claude Desktop Guide](https://claude.ai/desktop) - Client documentation
- [FastMCP Docs](https://github.com/modelcontextprotocol/python-sdk) - SDK reference

## Contributing

Improvements welcome! Areas for contribution:

- Additional tools (fine-tuning, evaluation, etc.)
- Better benchmark storage and retrieval
- Enhanced model selection algorithms
- Performance optimizations
- Documentation improvements

## License

MIT License - Same as GAMMA

---

**Made with ⚡️ by the GAMMA team**

Transform local LLM experimentation into an MCP-accessible service.
