export const MODEL_CATALOG = {
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
  'Xenova/distilgpt2': {
    id: 'Xenova/distilgpt2',
    name: 'DistilGPT2 82M',
    size: '82M',
    vram: '200MB',
    capabilities: ['tiny', 'fast'],
    recommended: false,
    engine: 'transformers',
    dtype: 'fp32'
  }
};

export const DEFAULT_MODEL = 'HuggingFaceTB/SmolLM2-360M-Instruct';