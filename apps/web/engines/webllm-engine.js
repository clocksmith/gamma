import { EngineInterface } from '../core/engine-interface.js';

export class WebLLMEngine extends EngineInterface {
  async load() {
    throw new Error('WebLLM support pending implementation');
  }
}