# GAMMA Integrations

Integration modules for using GAMMA engines with popular LLM frameworks.

## Modules

### OpenAI API Compatibility (`openai_compat.py`)

Wrap GAMMA engines to work with OpenAI SDK format.

**Quick Start:**
```python
from src.engines.pytorch_engine import PyTorchEngine
from src.integrations import OpenAICompatibleEngine

engine = PyTorchEngine("gpt2")
engine.load()

# Wrap with OpenAI compatibility
compat = OpenAICompatibleEngine(engine)

# Use OpenAI chat format
response = compat.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=50
)
print(response["choices"][0]["message"]["content"])
```

**Features:**
- Chat completions (`chat_completion`)
- Text completions (`completion`)
- Streaming support
- Multiple prompt templates (llama2, chatml, alpaca)

### LangChain Integration (`langchain_compat.py`)

Use GAMMA engines in LangChain chains and agents.

**Quick Start:**
```python
from src.engines.pytorch_engine import PyTorchEngine
from src.integrations import GAMMALangChainLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

engine = PyTorchEngine("gpt2")
engine.load()

# Create LangChain LLM
llm = GAMMALangChainLLM(engine=engine, max_tokens=50)

# Use in chains
prompt = PromptTemplate(
    input_variables=["question"],
    template="Question: {question}\nAnswer:"
)
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(question="What is Python?")
```

**Features:**
- `GAMMALangChainLLM` - LLM wrapper
- `GAMMAEmbeddings` - Embeddings wrapper
- Streaming support
- Chain/agent compatibility

### Ecosystem Utilities (`ecosystem_utils.py`)

Smart recommendations for frameworks and engines.

**Quick Start:**
```python
from src.integrations import (
    get_available_frameworks,
    suggest_framework_for_model,
    get_recommended_engine_for_model
)

# Check what's installed
frameworks = get_available_frameworks()
print(frameworks)  # {"vllm": False, "transformers": True, ...}

# Get recommendation for a model
rec = suggest_framework_for_model(
    model_name="llama-7b-q4.gguf",
    available_vram_gb=8
)
print(rec["primary"])  # "llama_cpp"

# Get GAMMA engine recommendation
engine_rec = get_recommended_engine_for_model(
    model_name="llama-7b-q4.gguf",
    use_case="speed"
)
print(engine_rec["engine"])  # "LlamaCppEngine"
```

**Functions:**
- `get_available_frameworks()` - Check installed frameworks
- `suggest_framework_for_model()` - Recommend framework for model
- `get_recommended_engine_for_model()` - Recommend GAMMA engine
- `suggest_optimizations()` - Get optimization tips
- `compare_frameworks()` - Framework comparison table

## Documentation

See [docs/integration-guide.md](../../docs/integration-guide.md) for comprehensive examples.
