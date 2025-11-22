export const MODEL_CATALOG = {
  // Gemma 3 - Mar 2025
  'onnx-community/gemma-3-1b-it-ONNX': {
    id: 'onnx-community/gemma-3-1b-it-ONNX',
    name: 'Gemma 3 1B',
    size: '1B',
    vram: '1.2GB',
    capabilities: ['balanced'],
    provider: 'google',
    released: 'Mar 2025',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // SmolLM2 - Nov 2024
  'HuggingFaceTB/SmolLM2-1.7B-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-1.7B-Instruct',
    name: 'SmolLM2 1.7B',
    size: '1.7B',
    vram: '2GB',
    capabilities: ['quality', 'smart'],
    provider: 'huggingface',
    released: 'Nov 2024',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4'
  },
  'HuggingFaceTB/SmolLM2-360M-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-360M-Instruct',
    name: 'SmolLM2 360M',
    size: '360M',
    vram: '400MB',
    capabilities: ['balanced', 'fast'],
    provider: 'huggingface',
    released: 'Nov 2024',
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
    provider: 'huggingface',
    released: 'Nov 2024',
    recommended: true,
    engine: 'transformers',
    dtype: 'fp16'
  },
  // Qwen 2.5 - Sep 2024
  'onnx-community/Qwen2.5-3B-Instruct': {
    id: 'onnx-community/Qwen2.5-3B-Instruct',
    name: 'Qwen 2.5 3B',
    size: '3B',
    vram: '3.5GB',
    capabilities: ['quality', 'coding'],
    provider: 'alibaba',
    released: 'Sep 2024',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  'onnx-community/Qwen2.5-1.5B-Instruct': {
    id: 'onnx-community/Qwen2.5-1.5B-Instruct',
    name: 'Qwen 2.5 1.5B',
    size: '1.5B',
    vram: '1.8GB',
    capabilities: ['quality', 'multilingual'],
    provider: 'alibaba',
    released: 'Sep 2024',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // Llama 3.2 - Sep 2024
  'onnx-community/Llama-3.2-3B-Instruct': {
    id: 'onnx-community/Llama-3.2-3B-Instruct',
    name: 'Llama 3.2 3B',
    size: '3B',
    vram: '3.5GB',
    capabilities: ['quality'],
    provider: 'meta',
    released: 'Sep 2024',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  'onnx-community/Llama-3.2-1B-Instruct': {
    id: 'onnx-community/Llama-3.2-1B-Instruct',
    name: 'Llama 3.2 1B',
    size: '1B',
    vram: '1.2GB',
    capabilities: ['balanced'],
    provider: 'meta',
    released: 'Sep 2024',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // Gemma 2 - Jun 2024
  'onnx-community/gemma-2-2b-it-ONNX': {
    id: 'onnx-community/gemma-2-2b-it-ONNX',
    name: 'Gemma 2 2B',
    size: '2B',
    vram: '2.5GB',
    capabilities: ['quality'],
    provider: 'google',
    released: 'Jun 2024',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // Phi-3 - Apr 2024
  'Xenova/Phi-3-mini-4k-instruct': {
    id: 'Xenova/Phi-3-mini-4k-instruct',
    name: 'Phi-3 Mini',
    size: '3.8B',
    vram: '4GB',
    capabilities: ['quality', 'reasoning'],
    provider: 'microsoft',
    released: 'Apr 2024',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4'
  }
};

export const DEFAULT_MODEL = 'HuggingFaceTB/SmolLM2-360M-Instruct';

// Provider colors for UI
export const PROVIDER_COLORS = {
  google: '#34a853',      // Green
  meta: '#0668e1',        // Blue
  alibaba: '#ff6a00',     // Orange
  microsoft: '#00bcf2',   // Light blue
  huggingface: '#ffcc00'  // Yellow
};
