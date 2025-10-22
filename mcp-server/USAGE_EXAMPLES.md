# GAMMA MCP Server - Usage Examples

Practical examples of using GAMMA through Claude Desktop's MCP integration.

## Basic Usage

### 1. Discover Available Models

**You ask:**
```
What LLM models do I have available on my system?
```

**Claude will:**
- Call `gamma://models/available` resource
- Show you all detected models from Ollama, HuggingFace, and local files
- Display hardware capabilities (GPU, VRAM, RAM)
- Group models by source

**Expected output:**
- List of models with sizes and memory requirements
- Hardware compatibility information
- Recommended engines for each model

---

### 2. Simple Inference

**You ask:**
```
Use GAMMA to generate a Python hello world program
```

**Claude will:**
- Auto-select an appropriate model
- Use `run_inference` tool
- Return generated code with performance metrics

**Expected output:**
- Generated Python code
- Model used
- Inference time
- Tokens per second

---

### 3. Model Comparison

**You ask:**
```
Compare gemma-2-2b and qwen2-1.5b on explaining what a REST API is
```

**Claude will:**
- Use `compare_models` tool with both models
- Run identical prompt on each
- Show side-by-side results

**Expected output:**
- Two different explanations
- Performance comparison
- Model characteristics

---

## Advanced Usage

### 4. Benchmarking

**You ask:**
```
Benchmark qwen3-coder:7b with 5 iterations to test its performance
```

**Claude will:**
- Use `benchmark_model` tool
- Run multiple test prompts
- Calculate average metrics

**Expected output:**
- Average tokens/second
- Latency statistics
- Best/worst throughput
- Memory usage

---

### 5. Smart Model Selection

**You ask:**
```
I need a model for code generation. I have 16GB VRAM and want the best
quality within that constraint. What should I use?
```

**Claude will:**
- Use `select_optimal_model` tool
- Analyze all available models
- Filter by VRAM constraint (16GB)
- Rank by quality priority

**Expected output:**
- Recommended model with rationale
- Alternative options
- Hardware requirements
- Expected performance

---

### 6. Specific Engine Selection

**You ask:**
```
Run inference using llama.cpp on qwen-coder with temperature 0.9,
top-k 50, and generate a binary search algorithm
```

**Claude will:**
- Use `run_inference` with specific parameters
- Force llama.cpp engine
- Apply custom sampling settings

**Expected output:**
- Generated binary search code
- Performance with specified parameters
- Engine used (llama.cpp)

---

## Workflow Examples

### 7. Model Selection Wizard

**You ask:**
```
Start the GAMMA model selection wizard to help me choose a model
```

**Claude will:**
- Activate `model_selection_wizard` prompt
- Ask about your task type
- Inquire about hardware constraints
- Question your priorities (speed/quality/balanced)
- Recommend optimal model

**Interactive flow:**
1. What's your task? → "Code generation"
2. What's your VRAM? → "24GB"
3. What's your priority? → "Quality"
4. **Result:** Recommendation with top 3 alternatives

---

### 8. Systematic Comparison

**You ask:**
```
Help me set up a comparison of multiple models for code generation tasks
```

**Claude will:**
- Activate `comparison_setup` prompt
- Guide you through defining test prompts
- Help select models to compare
- Run `compare_models` with your configuration

**Interactive flow:**
1. Define 3 test prompts
2. Select up to 4 models
3. Run comparison
4. Analyze results

---

## Real-World Scenarios

### 9. Finding the Fastest Model

**You ask:**
```
I need the fastest model available for chat, I don't care about quality.
Max 8GB VRAM.
```

**Claude response:**
- Filters models ≤8GB VRAM
- Prioritizes speed
- Recommends smallest quantized model
- Explains tradeoffs

---

### 10. Best Model for Specific Task

**You ask:**
```
Which GAMMA model is best for:
- Writing technical documentation
- Maximum 32GB VRAM
- Balanced speed/quality
```

**Claude response:**
- Analyzes "technical documentation" task
- Filters by 32GB VRAM
- Balances speed and quality
- Recommends mid-sized high-quality model

---

### 11. Hardware-Constrained Selection

**You ask:**
```
I only have a CPU, no GPU. What's the best model I can run?
```

**Claude response:**
- Identifies CPU-only constraint
- Recommends lightweight models
- Suggests llama.cpp engine
- Sets realistic expectations

---

### 12. Multi-Model Experiment

**You ask:**
```
I want to test 3 different sized models (2B, 7B, 13B) on writing
a React component. Show me the quality difference.
```

**Claude will:**
- Select representative models at each size
- Run `compare_models` with all three
- Show quality vs. performance tradeoff
- Help interpret results

---

## Engine-Specific Examples

### 13. Using PyTorch Engine

**You ask:**
```
Use PyTorch engine to run inference on gemma-2-9b-it with 4-bit quantization
```

**Claude will:**
- Force PyTorch engine
- Apply quantization settings
- Generate response

---

### 14. Using llama.cpp for Speed

**You ask:**
```
Run the fastest possible inference using llama.cpp on any GGUF model
```

**Claude will:**
- Select llama.cpp engine
- Choose optimized GGUF model
- Maximize GPU layers
- Optimize for throughput

---

### 15. Ollama Model Access

**You ask:**
```
List all my Ollama models and use the largest one for inference
```

**Claude will:**
- Filter models by Ollama source
- Select largest available
- Run inference via Ollama wrapper

---

## Prompt Engineering Examples

### 16. Iterative Refinement

**First request:**
```
Generate a sorting algorithm using GAMMA
```

**Follow-up:**
```
That was too slow. Use a smaller model for faster results
```

**Claude will:**
- Remember previous context
- Select smaller/faster model
- Regenerate with new constraints

---

### 17. A/B Testing

**You ask:**
```
Generate two versions of a login form component:
1. Using gemma-2-2b (fast)
2. Using qwen-coder-32b (quality)

Show me the difference in code quality.
```

**Claude will:**
- Run both models in parallel
- Compare outputs
- Analyze quality differences
- Show performance metrics

---

## Troubleshooting with GAMMA

### 18. Diagnosing Model Issues

**You ask:**
```
Why is my inference so slow? Can GAMMA benchmark my current setup?
```

**Claude will:**
- Run hardware detection
- Benchmark current configuration
- Identify bottlenecks
- Suggest optimizations

---

### 19. Finding Compatible Models

**You ask:**
```
I have 8GB VRAM and need a model for Python code generation.
Show me all compatible options.
```

**Claude will:**
- List all models ≤8GB VRAM
- Filter for code-capable models
- Rank by suitability
- Provide multiple options

---

## Power User Examples

### 20. Custom Benchmark Suite

**You ask:**
```
Benchmark these 3 models on these 5 specific prompts:

Models: gemma-2-2b, qwen-1.5b, phi-3-mini
Prompts:
1. Explain recursion
2. Write a binary search
3. Debug this code: [code]
4. Optimize this query: [sql]
5. Design a REST API for [domain]
```

**Claude will:**
- Run systematic comparison
- Execute all model/prompt combinations
- Generate performance matrix
- Analyze strengths/weaknesses

---

### 21. Resource-Aware Batch Processing

**You ask:**
```
I need to generate 10 different code snippets but want to use the optimal
model for each task within my 16GB VRAM limit.
```

**Claude will:**
- Analyze each task type
- Select best model per task
- Ensure VRAM constraint
- Batch efficiently

---

### 22. Mind Meld Experimentation

**You ask:**
```
Can GAMMA do Mind Meld? Show me how to blend gemma and qwen outputs.
```

**Claude will:**
- Explain Mind Meld capabilities
- Reference engine support
- Provide setup instructions
- Note experimental status

---

## Tips and Tricks

### Getting Better Results

1. **Be specific about constraints:**
   ```
   "Within 8GB VRAM" is better than "on a small GPU"
   ```

2. **Specify priorities:**
   ```
   "Prioritize speed over quality" gives clearer guidance
   ```

3. **Name models explicitly:**
   ```
   "Use qwen3-coder:30b" vs "use a code model"
   ```

4. **Combine operations:**
   ```
   "Benchmark then use the fastest model for my task"
   ```

### Understanding Outputs

- **Tokens/sec** - Higher is faster
- **Latency** - Lower is better
- **VRAM** - Must fit in your GPU memory
- **Size GB** - Larger often means better quality

### Common Patterns

```
List models → Select optimal → Run inference → Benchmark → Compare
```

This workflow maximizes GAMMA's capabilities through Claude's natural language interface.
