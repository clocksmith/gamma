import { MathUtils } from '../utils/math.js';
import { VocabularyTranslator } from './vocabulary-translator.js';
import { LogitBlender } from './logit-blender.js';
import { ABEEnsemble } from './abe-ensemble.js';
import { FixedIntervalStrategy, ConfidenceBasedStrategy } from './swap-strategies.js';
import { EventBus } from '../utils/event-bus.js';

export class MeldEngine {
  constructor(engines, config) {
    this.engines = engines;
    this.config = config;
    this.activeIndex = 0;
    this.vocabTranslator = new VocabularyTranslator();
    this.tokenHistory = [];
    
    this.swapStrategy = config.swapStrategy === 'confidence' 
      ? new ConfidenceBasedStrategy() 
      : new FixedIntervalStrategy();
      
    this.blender = config.useBlending ? new LogitBlender() : null;
    this.abeEnsemble = config.useABE ? new ABEEnsemble() : null;
  }

  async generateToken(context) {
    const predictions = await Promise.all(
      this.engines.map(engine => engine.predictNext(engine.encode(context), this.config))
    );

    let finalLogits;

    if (this.blender) {
      finalLogits = this.blender.blend(predictions.map(p => p.logitsProcessed));
    } else {
      finalLogits = predictions[this.activeIndex].logitsProcessed;
      const lastToken = this.tokenHistory[this.tokenHistory.length - 1] || '';
      
      if (this.swapStrategy.shouldSwap(lastToken, predictions, this.activeIndex)) {
        const newIndex = this.swapStrategy.selectNext(predictions, this.activeIndex);
        EventBus.emit('meld:swap', {
          from: this.activeIndex,
          to: newIndex,
          reason: this.swapStrategy.lastReason
        });
        this.activeIndex = newIndex;
        finalLogits = predictions[this.activeIndex].logitsProcessed;
      }
    }

    const probs = MathUtils.softmax(finalLogits);
    const tokenId = MathUtils.argmax(probs);
    const tokenText = this.engines[this.activeIndex].getTokenText(tokenId);

    this.tokenHistory.push(tokenText);

    return {
      tokenId,
      tokenText,
      activeModel: this.activeIndex
    };
  }
}