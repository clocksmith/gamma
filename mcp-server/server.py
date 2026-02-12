#!/usr/bin/env python3
"""
GAMMA MCP Server

Model Context Protocol server that exposes GAMMA's LLM experimentation
toolkit capabilities including model inference, comparison, and benchmarking.
"""
import sys
import os
import json
import logging
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path to import GAMMA modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (STDIO requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("gamma-mcp-server")

# Initialize FastMCP server
mcp = FastMCP("gamma",
              instructions="""GAMMA MCP Server provides access to a comprehensive LLM
              experimentation toolkit. Use this server to run inference on local models,
              compare different models side-by-side, benchmark performance, and get
              intelligent model recommendations based on your requirements.""")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_gamma_available_models() -> dict[str, Any]:
    """Get all available models detected by GAMMA."""
    try:
        from src.core.models.model_discovery import discover_all_models
        from src.core.hardware.gpu_discovery import get_gpu_info

        gpu_info = get_gpu_info()
        models = discover_all_models()

        # Extract hardware info from GPU discovery
        gpu_available = len(gpu_info) > 0
        gpu_name = gpu_info[0].name if gpu_available else "N/A"
        vram_gb = gpu_info[0].memory_total / (1024**3) if gpu_available and gpu_info[0].memory_total else 0

        return {
            "hardware": {
                "gpu_available": gpu_available,
                "gpu_name": gpu_name,
                "total_ram_gb": 0,  # RAM detection not in gpu_discovery
                "available_vram_gb": round(vram_gb, 1),
            },
            "models": models,
            "total_count": len(models)
        }
    except Exception as e:
        logger.error(f"Error discovering models: {e}")
        return {
            "hardware": {},
            "models": [],
            "total_count": 0,
            "error": str(e)
        }

def get_engine_capabilities() -> dict[str, Any]:
    """Get available inference engines and their capabilities."""
    engines = {
        "pytorch": {
            "name": "PyTorch",
            "description": "Native Transformers engine for HuggingFace models",
            "logits_access": "full",
            "mind_meld_support": True,
            "gpu_support": ["CUDA", "ROCm", "MPS"],
            "status": "stable"
        },
        "llamacpp": {
            "name": "llama.cpp",
            "description": "Optimized engine for GGUF quantized models",
            "logits_access": "full",
            "mind_meld_support": True,
            "gpu_support": ["CUDA", "ROCm", "Metal"],
            "status": "stable"
        },
        "vllm": {
            "name": "vLLM",
            "description": "High-throughput inference server",
            "logits_access": "full",
            "mind_meld_support": True,
            "gpu_support": ["CUDA"],
            "status": "stable"
        },
        "ollama": {
            "name": "Ollama",
            "description": "HTTP API wrapper for local models",
            "logits_access": "synthetic",
            "mind_meld_support": "limited",
            "gpu_support": ["any"],
            "status": "stable"
        },
        "mlx": {
            "name": "MLX",
            "description": "Apple Silicon optimized inference",
            "logits_access": "full",
            "mind_meld_support": True,
            "gpu_support": ["Apple M1/M2/M3/M4"],
            "status": "experimental"
        }
    }
    return engines

def format_model_info(model: dict) -> str:
    """Format a single model's information for display."""
    lines = [
        f"**{model.get('name', 'Unknown')}**",
        f"  Source: {model.get('source', 'Unknown')}",
        f"  Engine: {model.get('recommended_engine', 'auto')}",
    ]

    if 'size_gb' in model:
        lines.append(f"  Size: {model['size_gb']:.2f} GB")

    if 'vram_required_gb' in model:
        lines.append(f"  VRAM Required: {model['vram_required_gb']:.2f} GB")

    return "\n".join(lines)

# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("gamma://models/available")
def list_available_models() -> str:
    """List all models detected by GAMMA from Ollama, HuggingFace, and local files.

    Returns a comprehensive listing of available models with hardware requirements
    and recommended inference engines.
    """
    data = get_gamma_available_models()

    if data.get("error"):
        return f"Error discovering models: {data['error']}"

    output = ["# Available Models\n"]
    output.append(f"**Total Models Found:** {data['total_count']}\n")

    # Hardware info
    hw = data.get("hardware", {})
    output.append("## Hardware Configuration")
    output.append(f"- GPU Available: {hw.get('gpu_available', False)}")
    if hw.get('gpu_name'):
        output.append(f"- GPU: {hw['gpu_name']}")
    output.append(f"- System RAM: {hw.get('total_ram_gb', 0):.1f} GB")
    output.append(f"- Available VRAM: {hw.get('available_vram_gb', 0):.1f} GB\n")

    # Group models by source
    models_by_source = {}
    for model in data.get("models", []):
        source = model.get("source", "unknown")
        if source not in models_by_source:
            models_by_source[source] = []
        models_by_source[source].append(model)

    # Display by source
    for source, models in models_by_source.items():
        output.append(f"\n## {source.capitalize()} Models ({len(models)})")
        for model in models[:10]:  # Limit to 10 per source
            output.append(format_model_info(model))

        if len(models) > 10:
            output.append(f"\n_...and {len(models) - 10} more models_")

    return "\n".join(output)

@mcp.resource("gamma://engines/status")
def get_engines_status() -> str:
    """Get status and capabilities of all GAMMA inference engines.

    Returns detailed information about each engine including GPU support,
    logits access, and Mind Meld compatibility.
    """
    engines = get_engine_capabilities()

    output = ["# GAMMA Inference Engines\n"]

    for engine_id, info in engines.items():
        output.append(f"## {info['name']} (`{engine_id}`)")
        output.append(f"**Description:** {info['description']}")
        output.append(f"**Status:** {info['status']}")
        output.append(f"**Logits Access:** {info['logits_access']}")
        output.append(f"**Mind Meld Support:** {info['mind_meld_support']}")
        output.append(f"**GPU Support:** {', '.join(info['gpu_support'])}\n")

    return "\n".join(output)

@mcp.resource("gamma://benchmarks/{model_id}")
def get_model_benchmarks(model_id: str) -> str:
    """Get benchmark results for a specific model.

    Args:
        model_id: Model identifier (e.g., 'gemma-2-2b-it', 'qwen3-coder:30b')

    Returns historical benchmark data if available, including performance metrics.
    """
    # This would integrate with GAMMA's benchmark storage
    # For now, return a template response
    return f"""# Benchmark Results: {model_id}

**Note:** Benchmark data not yet implemented. Run benchmarks using the
`benchmark_model` tool to generate performance metrics.

To benchmark this model, use:
```
benchmark_model(model="{model_id}", engine="auto", iterations=5)
```

Benchmark metrics include:
- Tokens per second (throughput)
- Time to first token (latency)
- Memory usage (RAM/VRAM)
- Code generation quality (TS vs JS benchmark suite)
- Reasoning accuracy
"""

# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool()
async def run_inference(
    prompt: str,
    model: str = "auto",
    engine: str = "auto",
    max_tokens: int = 100,
    temperature: float = 0.7,
    top_k: int = 40,
    top_p: float = 0.95
) -> str:
    """Run inference on a prompt using specified model and engine.

    Args:
        prompt: The input text prompt
        model: Model name/path or 'auto' for automatic selection
        engine: Engine to use (pytorch, llamacpp, vllm, ollama) or 'auto'
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.1-2.0)
        top_k: Top-K filtering
        top_p: Nucleus sampling threshold

    Returns generated text with performance metadata.
    """
    try:
        # Import GAMMA's inference engine
        from src.engines.engine_factory import get_engine

        logger.info(f"Running inference with model={model}, engine={engine}")

        # Auto-select model if needed
        if model == "auto":
            models = get_gamma_available_models()
            if models.get("models"):
                model = models["models"][0].get("name", "gemma-2-2b-it")
                logger.info(f"Auto-selected model: {model}")
            else:
                return "Error: No models available. Please install Ollama or download models."

        # Get engine instance
        engine_config = {
            'temperature': temperature,
            'top_k': top_k,
            'top_p': top_p,
            'max_tokens': max_tokens
        }

        eng = get_engine(engine, model, engine_config)

        # Run inference
        import time
        start_time = time.time()
        response = eng.generate(prompt, max_tokens=max_tokens)
        elapsed = time.time() - start_time

        # Format response
        output = [
            "# Inference Result\n",
            f"**Model:** {model}",
            f"**Engine:** {engine}",
            f"**Time:** {elapsed:.2f}s",
            f"**Tokens/sec:** {max_tokens/elapsed:.1f}\n",
            "## Generated Text",
            response,
        ]

        return "\n".join(output)

    except Exception as e:
        logger.error(f"Inference error: {e}")
        return f"Error during inference: {str(e)}"

@mcp.tool()
async def compare_models(
    prompt: str,
    models: list[str],
    engine: str = "auto",
    max_tokens: int = 50
) -> str:
    """Compare multiple models on the same prompt side-by-side.

    Args:
        prompt: Input text to compare across models
        models: List of model identifiers to compare
        engine: Engine to use for all models or 'auto'
        max_tokens: Maximum tokens per generation

    Returns side-by-side comparison with outputs and performance metrics.
    """
    if len(models) > 4:
        return "Error: Maximum 4 models can be compared at once"

    if len(models) < 2:
        return "Error: At least 2 models required for comparison"

    results = []

    for model in models:
        result = await run_inference(
            prompt=prompt,
            model=model,
            engine=engine,
            max_tokens=max_tokens
        )
        results.append(f"### {model}\n{result}")

    output = [
        "# Model Comparison Results\n",
        f"**Prompt:** {prompt}\n",
        "---\n"
    ]
    output.extend(results)

    return "\n".join(output)

@mcp.tool()
async def benchmark_model(
    model: str,
    engine: str = "auto",
    iterations: int = 3,
    tokens: int = 100
) -> str:
    """Run comprehensive benchmarks on a model.

    Args:
        model: Model identifier to benchmark
        engine: Engine to use or 'auto'
        iterations: Number of benchmark iterations
        tokens: Tokens to generate per iteration

    Returns detailed performance metrics including throughput and latency.
    """
    try:
        logger.info(f"Benchmarking {model} with {iterations} iterations")

        import time
        results = []

        test_prompts = [
            "Explain quantum computing in simple terms.",
            "Write a Python function to calculate fibonacci numbers.",
            "What are the benefits of functional programming?"
        ]

        for i in range(min(iterations, len(test_prompts))):
            start = time.time()
            result = await run_inference(
                prompt=test_prompts[i],
                model=model,
                engine=engine,
                max_tokens=tokens
            )
            elapsed = time.time() - start
            results.append({
                "iteration": i + 1,
                "time": elapsed,
                "tokens_per_sec": tokens / elapsed if elapsed > 0 else 0
            })

        # Calculate averages
        avg_time = sum(r["time"] for r in results) / len(results)
        avg_tps = sum(r["tokens_per_sec"] for r in results) / len(results)

        output = [
            f"# Benchmark Results: {model}\n",
            f"**Engine:** {engine}",
            f"**Iterations:** {iterations}",
            f"**Tokens per iteration:** {tokens}\n",
            "## Performance Metrics",
            f"- **Average Time:** {avg_time:.2f}s",
            f"- **Average Throughput:** {avg_tps:.1f} tokens/sec",
            f"- **Best Throughput:** {max(r['tokens_per_sec'] for r in results):.1f} tokens/sec",
            f"- **Worst Throughput:** {min(r['tokens_per_sec'] for r in results):.1f} tokens/sec",
        ]

        return "\n".join(output)

    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        return f"Error during benchmarking: {str(e)}"

@mcp.tool()
async def select_optimal_model(
    task_description: str,
    max_vram_gb: float = 24.0,
    max_latency_sec: float = 5.0,
    priority: str = "balanced"
) -> str:
    """Intelligently select the best model for a given task and constraints.

    Args:
        task_description: Description of the task (e.g., 'code generation', 'chat', 'reasoning')
        max_vram_gb: Maximum VRAM available in GB
        max_latency_sec: Maximum acceptable latency in seconds
        priority: Optimization priority ('speed', 'quality', 'balanced')

    Returns recommended model with rationale.
    """
    models_data = get_gamma_available_models()
    hw = models_data.get("hardware", {})
    models = models_data.get("models", [])

    if not models:
        return "Error: No models available for selection"

    # Filter by VRAM constraint
    suitable_models = [
        m for m in models
        if m.get("vram_required_gb", 0) <= max_vram_gb
    ]

    if not suitable_models:
        return f"Error: No models fit within {max_vram_gb}GB VRAM constraint"

    # Simple scoring based on priority
    scored_models = []
    for model in suitable_models:
        score = 0
        size = model.get("size_gb", 10)

        if priority == "speed":
            # Prefer smaller models
            score = 100 / (size + 1)
        elif priority == "quality":
            # Prefer larger models
            score = size
        else:  # balanced
            score = 50 if 2 < size < 10 else 30

        # Bonus for recommended engine availability
        if model.get("recommended_engine") in ["llamacpp", "pytorch"]:
            score += 10

        scored_models.append((score, model))

    # Sort by score
    scored_models.sort(reverse=True, key=lambda x: x[0])
    top_model = scored_models[0][1]

    output = [
        "# Model Selection Recommendation\n",
        f"**Task:** {task_description}",
        f"**Priority:** {priority}",
        f"**VRAM Limit:** {max_vram_gb}GB\n",
        "## Recommended Model",
        f"**Name:** {top_model.get('name', 'Unknown')}",
        f"**Source:** {top_model.get('source', 'Unknown')}",
        f"**Engine:** {top_model.get('recommended_engine', 'auto')}",
        f"**Size:** {top_model.get('size_gb', 0):.2f} GB",
        f"**VRAM Required:** {top_model.get('vram_required_gb', 0):.2f} GB\n",
        "## Rationale",
        f"Selected based on {priority} optimization within hardware constraints.",
        f"\n**Alternative Options:**"
    ]

    # Show top 3 alternatives
    for i, (score, model) in enumerate(scored_models[1:4], 2):
        output.append(f"{i}. {model.get('name')} ({model.get('size_gb', 0):.1f}GB)")

    return "\n".join(output)

# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def model_selection_wizard() -> list[dict]:
    """Interactive wizard to help select the right model for your task.

    Guides users through hardware constraints, task requirements, and
    performance preferences to recommend optimal model configuration.
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": """I need help selecting the best LLM model for my task. Please ask me:

1. What task do I want to perform? (code generation, chat, reasoning, etc.)
2. What are my hardware constraints? (available VRAM, RAM)
3. What's my priority? (speed, quality, or balanced)
4. Do I need specific features? (function calling, long context, etc.)

Then use the select_optimal_model tool to recommend the best option."""
            }
        }
    ]

@mcp.prompt()
def comparison_setup() -> list[dict]:
    """Setup template for comparing multiple models systematically.

    Provides structure for running consistent comparisons across different
    models with the same test prompts and evaluation criteria.
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": """Help me compare multiple LLM models. I need to:

1. Define my test prompts (provide 2-3 representative examples)
2. Select which models to compare (up to 4)
3. Choose evaluation criteria (speed, quality, consistency)

Then use the compare_models tool to run the comparison and analyze results."""
            }
        }
    ]

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Initialize and run the GAMMA MCP server."""
    logger.info("Starting GAMMA MCP Server...")

    # Run server with stdio transport (for Claude Desktop)
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
