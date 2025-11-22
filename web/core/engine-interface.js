export class EngineInterface {
  constructor(modelId, config = {}) {
    this.modelId = modelId;
    this.config = config;
    this.ready = false;
  }

  async load() { throw new Error('Not implemented'); }
  encode(text) { throw new Error('Not implemented'); }
  decode(tokenIds) { throw new Error('Not implemented'); }
  async predictNext(inputIds, samplingConfig) { throw new Error('Not implemented'); }
  getVocabularySize() { throw new Error('Not implemented'); }
  getTokenText(tokenId) { throw new Error('Not implemented'); }
  isSpecialToken(tokenId) { throw new Error('Not implemented'); }
}