import { MathUtils } from '../utils/math.js';

export class SwapStrategyBase {
  shouldSwap(lastToken, predictions, activeIndex) { throw new Error('Abstract'); }
  selectNext(predictions, currentIndex) { throw new Error('Abstract'); }
}

export class FixedIntervalStrategy extends SwapStrategyBase {
  constructor(interval = 5) {
    super();
    this.interval = interval;
    this.counter = 0;
  }

  shouldSwap() {
    this.counter++;
    if (this.counter >= this.interval) {
      this.counter = 0;
      this.lastReason = `Fixed interval (${this.interval} tokens)`;
      return true;
    }
    return false;
  }

  selectNext(predictions, currentIndex) {
    return (currentIndex + 1) % predictions.length;
  }
}

export class ConfidenceBasedStrategy extends SwapStrategyBase {
  constructor(threshold = 0.3) {
    super();
    this.threshold = threshold;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const activePred = predictions[activeIndex];
    const topProb = Math.max(...MathUtils.softmax(activePred.logitsProcessed));

    if (topProb < this.threshold) {
      this.lastReason = `Low confidence: ${(topProb * 100).toFixed(1)}%`;
      return true;
    }
    return false;
  }

  selectNext(predictions, currentIndex) {
    let maxConf = 0;
    let bestIdx = currentIndex;
    predictions.forEach((pred, idx) => {
      const conf = Math.max(...MathUtils.softmax(pred.logitsProcessed));
      if (conf > maxConf) {
        maxConf = conf;
        bestIdx = idx;
      }
    });
    return bestIdx;
  }
}