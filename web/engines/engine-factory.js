import { TransformersEngine } from './transformers-engine.js';
import { MODEL_CATALOG } from '../core/model-registry.js';

export const EngineFactory = {
  getEngine(modelId) {
    const config = MODEL_CATALOG[modelId];
    if (!config) {
      throw new Error(`Model ${modelId} not found in registry`);
    }

    switch (config.engine) {
      case 'transformers':
        return new TransformersEngine(modelId, config);
      default:
        throw new Error(`Unknown engine type: ${config.engine}`);
    }
  }
};