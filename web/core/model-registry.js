export const MODEL_CATALOG = {
  // SmolLM2 - Nov 2024
  'HuggingFaceTB/SmolLM2-1.7B-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-1.7B-Instruct',
    name: 'SmolLM2 1.7B',
    size: '1.7B',
    downloadSize: '1.0GB',
    vram: '2GB',
    capabilities: ['quality', 'smart'],
    provider: 'huggingface',
    released: 'Nov 24',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4'
  },
  'HuggingFaceTB/SmolLM2-360M-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-360M-Instruct',
    name: 'SmolLM2 360M',
    size: '360M',
    downloadSize: '724MB',
    vram: '400MB',
    capabilities: ['balanced', 'fast'],
    provider: 'huggingface',
    released: 'Nov 24',
    recommended: true,
    engine: 'transformers',
    dtype: 'fp16'
  },
  'HuggingFaceTB/SmolLM2-135M-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-135M-Instruct',
    name: 'SmolLM2 135M',
    size: '135M',
    downloadSize: '270MB',
    vram: '200MB',
    capabilities: ['ultra-fast', 'lightweight'],
    provider: 'huggingface',
    released: 'Nov 24',
    recommended: true,
    engine: 'transformers',
    dtype: 'fp16'
  },
  // Qwen 2.5 - Sep 2024
  'onnx-community/Qwen2.5-1.5B-Instruct': {
    id: 'onnx-community/Qwen2.5-1.5B-Instruct',
    name: 'Qwen 2.5 1.5B',
    size: '1.5B',
    downloadSize: '950MB',
    vram: '1.8GB',
    capabilities: ['quality', 'multilingual'],
    provider: 'alibaba',
    released: 'Sep 24',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  'onnx-community/Qwen2.5-0.5B-Instruct': {
    id: 'onnx-community/Qwen2.5-0.5B-Instruct',
    name: 'Qwen 2.5 0.5B',
    size: '0.5B',
    downloadSize: '350MB',
    vram: '600MB',
    capabilities: ['fast', 'multilingual'],
    provider: 'alibaba',
    released: 'Sep 24',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // Llama 3.2 - Sep 2024
  'onnx-community/Llama-3.2-1B-Instruct': {
    id: 'onnx-community/Llama-3.2-1B-Instruct',
    name: 'Llama 3.2 1B',
    size: '1B',
    downloadSize: '700MB',
    vram: '1.2GB',
    capabilities: ['balanced'],
    provider: 'meta',
    released: 'Sep 24',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  },
  // TinyLlama - Jan 2024
  'onnx-community/TinyLlama-1.1B-Chat-v1.0': {
    id: 'onnx-community/TinyLlama-1.1B-Chat-v1.0',
    name: 'TinyLlama 1.1B',
    size: '1.1B',
    downloadSize: '600MB',
    vram: '1.2GB',
    capabilities: ['balanced', 'fast'],
    provider: 'tinyllama',
    released: 'Jan 24',
    recommended: false,
    engine: 'transformers',
    dtype: 'q4f16'
  }
};

// Helper to categorize models by size
export const MODEL_SIZE_CATEGORIES = {
  small: ['HuggingFaceTB/SmolLM2-135M-Instruct', 'HuggingFaceTB/SmolLM2-360M-Instruct', 'onnx-community/Qwen2.5-0.5B-Instruct'],
  medium: ['onnx-community/TinyLlama-1.1B-Chat-v1.0', 'onnx-community/Llama-3.2-1B-Instruct', 'onnx-community/Qwen2.5-1.5B-Instruct', 'HuggingFaceTB/SmolLM2-1.7B-Instruct'],
  experimental: []
};

export const DEFAULT_MODEL = 'HuggingFaceTB/SmolLM2-360M-Instruct';

// Provider colors for UI
export const PROVIDER_COLORS = {
  google: '#34a853',      // Green
  meta: '#0668e1',        // Blue
  alibaba: '#ff6a00',     // Orange
  microsoft: '#00bcf2',   // Light blue
  huggingface: '#ffcc00', // Yellow
  tinyllama: '#9b59b6'    // Purple
};
