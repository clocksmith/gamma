# Integration Guide

How to integrate GAMMA engines with popular LLM frameworks and tools.

## Table of Contents

- [OpenAI API Compatibility](#openai-api-compatibility)
- [LangChain Integration](#langchain-integration)
- [Framework Selection](#framework-selection)
- [Configuration Conversion](#configuration-conversion)

---

## OpenAI API Compatibility

Use GAMMA engines with OpenAI-compatible request/response formats.

### Chat Completions

```python
from src.engines.pytorch_engine import PyTorchEngine
from src.integrations import OpenAICompatibleEngine

# Setup engine
engine = PyTorchEngine("gpt2")
engine.load()

# Wrap with OpenAI compatibility
compat = OpenAICompatibleEngine(engine)

# Chat format
response = compat.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response["choices"][0]["message"]["content"])
```

### Text Completions

```python
response = compat.completion(
    prompt="The future of AI is",
    max_tokens=50,
    temperature=0.8,
    stop=["\n"]
)

print(response["choices"][0]["text"])
```

### Streaming

```python
for chunk in compat.chat_completion(
    messages=[{"role": "user", "content": "Tell me a story"}],
    max_tokens=100,
    stream=True
):
    print(chunk["choices"][0]["delta"].get("content", ""), end="")
```

### Custom Prompt Templates

```python
from src.integrations import messages_to_prompt

messages = [
    {"role": "system", "content": "You are helpful"},
    {"role": "user", "content": "Hello"}
]

# Llama 2 format
prompt = messages_to_prompt(messages, template="llama2")

# ChatML format (GPT-4, Mistral)
prompt = messages_to_prompt(messages, template="chatml")

# Alpaca format
prompt = messages_to_prompt(messages, template="alpaca")
```

---

## LangChain Integration

Use GAMMA engines in LangChain applications.

### Basic LLM Usage

```python
from src.engines.pytorch_engine import PyTorchEngine
from src.integrations import GAMMALangChainLLM

engine = PyTorchEngine("gpt2")
engine.load()

llm = GAMMALangChainLLM(
    engine=engine,
    max_tokens=50,
    temperature=0.7
)

# Direct call
result = llm("What is machine learning?")
print(result)
```

### Using in Chains

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["topic"],
    template="Write a short explanation of {topic}:"
)

chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(topic="neural networks")
print(result)
```

### Sequential Chains

```python
from langchain.chains import SimpleSequentialChain

# First chain: generate idea
idea_prompt = PromptTemplate(
    input_variables=["topic"],
    template="Generate a creative idea about {topic}:"
)
idea_chain = LLMChain(llm=llm, prompt=idea_prompt)

# Second chain: expand idea
expand_prompt = PromptTemplate(
    input_variables=["idea"],
    template="Expand on this idea: {idea}"
)
expand_chain = LLMChain(llm=llm, prompt=expand_prompt)

# Combine
full_chain = SimpleSequentialChain(
    chains=[idea_chain, expand_chain],
    verbose=True
)

result = full_chain.run("sustainable energy")
```

### Embeddings (for RAG)

```python
from src.integrations import GAMMAEmbeddings

# Requires engine with hidden state support
embeddings = GAMMAEmbeddings(
    engine=engine,
    pooling="mean"
)

# Embed documents
docs = [
    "Machine learning is a subset of AI",
    "Deep learning uses neural networks"
]
doc_embeddings = embeddings.embed_documents(docs)

# Embed query
query = "What is deep learning?"
query_embedding = embeddings.embed_query(query)

# Use with vector stores
from langchain.vectorstores import FAISS

vectorstore = FAISS.from_documents(documents, embeddings)
results = vectorstore.similarity_search(query, k=3)
```

---

## Framework Selection

Get intelligent recommendations for which framework to use.

### Check Available Frameworks

```python
from src.integrations import (
    get_available_frameworks,
    print_available_frameworks
)

frameworks = get_available_frameworks()
print(frameworks)
# {"vllm": False, "exllamav2": False, "transformers": True, ...}

print_available_frameworks()
# Prints formatted table
```

### Get Model Recommendations

```python
from src.integrations import suggest_framework_for_model

# For GGUF models
rec = suggest_framework_for_model(
    model_name="llama-7b-q4.gguf",
    model_format="gguf",
    available_vram_gb=8
)

print(rec["primary"])      # "llama_cpp"
print(rec["reason"])       # "GGUF format is natively supported..."
print(rec["alternatives"]) # ["GAMMA LlamaCppEngine"]

# For GPTQ models
rec = suggest_framework_for_model(
    model_name="llama-7b-gptq",
    model_format="gptq"
)

print(rec["primary"])  # "exllamav2"
```

### Get GAMMA Engine Recommendations

```python
from src.integrations import get_recommended_engine_for_model

# For GGUF file
rec = get_recommended_engine_for_model(
    model_name="model.gguf",
    use_case="speed"
)

print(rec["engine"])  # "LlamaCppEngine"
print(rec["config"])  # {"n_gpu_layers": -1, ...}

# For Ollama format
rec = get_recommended_engine_for_model(
    model_name="llama2:7b",
    use_case="low_memory"
)

print(rec["engine"])  # "OllamaEngine"
```

### Optimization Suggestions

```python
from src.integrations import suggest_optimizations

suggestions = suggest_optimizations(
    engine_type="PyTorchEngine",
    model_size_gb=13.5,
    available_vram_gb=8.0
)

for suggestion in suggestions:
    print(suggestion)

# Output:
# ⚠ Model (13.5GB) larger than VRAM (8.0GB). Consider:
#   - Quantization (use GGUF Q4/Q5 models)
#   - CPU offloading (set n_gpu_layers for llama.cpp)
#   - Smaller model variant
# 💡 PyTorch optimizations:
#   - Use torch.compile() for faster inference (PyTorch 2.0+)
#   - Enable flash attention if available
#   - Use bfloat16 for better performance/quality balance
```

---

## Configuration Conversion

Convert between different framework configurations.

### GAMMA to vLLM

```python
from src.integrations.ecosystem_utils import convert_gamma_config_to_vllm

gamma_config = {
    "temperature": 0.7,
    "top_k": 50,
    "top_p": 0.9,
    "max_tokens": 100
}

vllm_params = convert_gamma_config_to_vllm(gamma_config)
# Use with vLLM SamplingParams
```

### GAMMA to Transformers

```python
from src.integrations.ecosystem_utils import convert_gamma_config_to_transformers

transformers_params = convert_gamma_config_to_transformers(gamma_config)
# Use with model.generate()
```

---

## Complete Examples

### Example 1: Using with Existing OpenAI Code

```python
# Minimal changes to existing OpenAI code
from src.engines.pytorch_engine import PyTorchEngine
from src.integrations import OpenAICompatibleEngine

# Replace OpenAI client with GAMMA
engine = PyTorchEngine("gpt2")
engine.load()
client = OpenAICompatibleEngine(engine)

# Rest of code stays the same
response = client.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=50
)
```

### Example 2: LangChain RAG Pipeline

```python
from src.engines.pytorch_engine import PyTorchEngine
from src.integrations import GAMMALangChainLLM, GAMMAEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA

# Setup
engine = PyTorchEngine("sentence-transformers/all-MiniLM-L6-v2")
engine.load()

llm = GAMMALangChainLLM(engine=engine)
embeddings = GAMMAEmbeddings(engine=engine)

# Process documents
text_splitter = CharacterTextSplitter(chunk_size=1000)
texts = text_splitter.split_text(long_document)

# Create vector store
vectorstore = FAISS.from_texts(texts, embeddings)

# Create QA chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

# Query
answer = qa.run("What is the main topic?")
```

---

## Installation Notes

### LangChain
```bash
pip install langchain
```

### Optional Frameworks
```bash
# For recommendations only (not required)
pip install vllm              # Fast inference
pip install exllamav2         # GPTQ models
pip install llama-cpp-python  # GGUF models
```

---

## Troubleshooting

### LangChain Import Error

If you see: `ImportError: cannot import name 'LLM'`

**Solution:** Install LangChain
```bash
pip install langchain
```

### Hidden States Not Available

If embeddings fail with: `NotImplementedError: Engine ... does not support embeddings`

**Solution:** The engine needs a `get_hidden_states()` method. Currently supported by PyTorch-based engines only. Add to your engine:

```python
def get_hidden_states(self, input_ids, attention_mask):
    outputs = self.model(input_ids, attention_mask, output_hidden_states=True)
    return outputs.hidden_states[-1].detach().cpu().numpy()
```

---

## See Also

- [Optimization Guide](./optimization-guide.md) - Performance tuning
- [src/integrations/](../src/integrations/) - Integration module source
- [Examples](../examples/) - More complete examples
