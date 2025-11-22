export const MODEL_CATALOG = {
  // Row 1: SmolLM2 family
  'HuggingFaceTB/SmolLM2-360M-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-360M-Instruct',
    name: 'SmolLM2 360M',
    size: '360M',
    vram: '400MB',
    capabilities: ['balanced', 'fast'],
    recommended: true,
    engine: 'transformers',
    dtype: 'fp16'
  },
  'HuggingFaceTB/SmolLM2-135M-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-135M-Instruct',
    name: 'SmolLM2 135M',
    size: '135M',
    vram: '200MB',
    capabilities: ['ultra-fast', 'lightweight'],
    recommended: true,
    engine: 'transformers',
    dtype: 'fp16'
  },
  'HuggingFaceTB/SmolLM2-1.7B-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-1.7B-Instruct',
    name: 'SmolLM2 1.7B',
    size: '1.7B',
    vram: '2GB',
    capabilities: ['quality', 'smart'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4'
  },
  'Xenova/gpt2': {
    id: 'Xenova/gpt2',
    name: 'GPT-2 124M',
    size: '124M',
    vram: '300MB',
    capabilities: ['classic', 'stable'],
    recommended: false,
    engine: 'transformers',
    dtype: 'fp32'
  },
  // Row 2: GPT-2 variants and Phi
  'Xenova/gpt2-medium': {
    id: 'Xenova/gpt2-medium',
    name: 'GPT-2 Medium',
    size: '355M',
    vram: '700MB',
    capabilities: ['classic', 'balanced'],
    recommended: false,
    engine: 'transformers',
    dtype: 'fp32'
  },
  'Xenova/distilgpt2': {
    id: 'Xenova/distilgpt2',
    name: 'DistilGPT2 82M',
    size: '82M',
    vram: '200MB',
    capabilities: ['tiny', 'fast'],
    recommended: false,
    engine: 'transformers',
    dtype: 'fp32'
  },
  'Xenova/Phi-3-mini-4k-instruct': {
    id: 'Xenova/Phi-3-mini-4k-instruct',
    name: 'Phi-3 Mini',
    size: '3.8B',
    vram: '4GB',
    capabilities: ['quality', 'reasoning'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4'
  },
  'Xenova/LaMini-Flan-T5-248M': {
    id: 'Xenova/LaMini-Flan-T5-248M',
    name: 'LaMini T5',
    size: '248M',
    vram: '500MB',
    capabilities: ['instruction', 'fast'],
    recommended: false,
    engine: 'transformers',
    dtype: 'fp32'
  },
  // Gemma models
  'onnx-community/gemma-2-2b-it-ONNX': {
    id: 'onnx-community/gemma-2-2b-it-ONNX',
    name: 'Gemma 2 2B',
    size: '2B',
    vram: '2.5GB',
    capabilities: ['quality', 'google'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  'onnx-community/gemma-3-1b-it-ONNX': {
    id: 'onnx-community/gemma-3-1b-it-ONNX',
    name: 'Gemma 3 1B',
    size: '1B',
    vram: '1.2GB',
    capabilities: ['balanced', 'google'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // Qwen models
  'onnx-community/Qwen2.5-1.5B-Instruct': {
    id: 'onnx-community/Qwen2.5-1.5B-Instruct',
    name: 'Qwen 2.5 1.5B',
    size: '1.5B',
    vram: '1.8GB',
    capabilities: ['quality', 'multilingual'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  'onnx-community/Qwen2.5-3B-Instruct': {
    id: 'onnx-community/Qwen2.5-3B-Instruct',
    name: 'Qwen 2.5 3B',
    size: '3B',
    vram: '3.5GB',
    capabilities: ['quality', 'coding'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // Llama models
  'onnx-community/Llama-3.2-1B-Instruct': {
    id: 'onnx-community/Llama-3.2-1B-Instruct',
    name: 'Llama 3.2 1B',
    size: '1B',
    vram: '1.2GB',
    capabilities: ['balanced', 'meta'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  'onnx-community/Llama-3.2-3B-Instruct': {
    id: 'onnx-community/Llama-3.2-3B-Instruct',
    name: 'Llama 3.2 3B',
    size: '3B',
    vram: '3.5GB',
    capabilities: ['quality', 'meta'],
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  }
};

export const DEFAULT_MODEL = 'HuggingFaceTB/SmolLM2-360M-Instruct';