# Integration Guide

Use GAMMA engines with common API and framework surfaces.

## Integration Modules

The integration code lives in `src/integrations/`:

- `openai_compat.py`
- `langchain_compat.py`
- `ecosystem_utils.py`

## OpenAI-Compatible Wrapper

```python
from src.engines.native.pytorch_engine import PyTorchEngine
from src.integrations.openai_compat import OpenAICompatibleEngine

engine = PyTorchEngine("google/gemma-2-2b-it")
engine.load()
compat = OpenAICompatibleEngine(engine)

response = compat.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=50,
    temperature=0.7,
)
```

Supported surface:

- `chat_completion`
- `completion`
- streaming responses
- prompt templates (`llama2`, `chatml`, `alpaca`)

## LangChain Wrapper

```python
from src.engines.native.pytorch_engine import PyTorchEngine
from src.integrations.langchain_compat import GAMMALangChainLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

engine = PyTorchEngine("google/gemma-2-2b-it")
engine.load()
llm = GAMMALangChainLLM(engine=engine, max_tokens=100)

prompt = PromptTemplate(input_variables=["question"], template="Question: {question}\nAnswer:")
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(question="What is Python?")
```

Embeddings wrapper:

```python
from src.integrations.langchain_compat import GAMMAEmbeddings

embeddings = GAMMAEmbeddings(engine=engine)
vectors = embeddings.embed_documents(["Hello world", "Goodbye"])
```

## Ecosystem Recommendation Helpers

```python
from src.integrations.ecosystem_utils import (
    get_available_frameworks,
    suggest_framework_for_model,
    get_recommended_engine_for_model,
)

frameworks = get_available_frameworks()
framework_pick = suggest_framework_for_model(model_name="llama-7b-q4.gguf", available_vram_gb=8)
engine_pick = get_recommended_engine_for_model(model_name="llama-7b-q4.gguf", use_case="speed")
```

## API Server

```bash
python tools/run_api_server.py --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /v1/models`
- `POST /v1/completions`
- `POST /v1/chat/completions`
- `GET /health`

## MCP Integration

GAMMA also ships an MCP server. See [../mcp-server/README.md](../mcp-server/README.md).

## Notes

- Wrapper/API engines generally do not expose raw logits.
- Features that require logits (for example Mind Meld/certain comparison flows) must use native engines.
