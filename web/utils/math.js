export const MathUtils = {
  softmax(logits) {
    const maxLogit = Math.max(...logits);
    const exps = logits.map(l => Math.exp(l - maxLogit));
    const sumExps = exps.reduce((a, b) => a + b, 0);
    return exps.map(e => e / sumExps);
  },

  calculateEntropy(probs) {
    return -probs.reduce((sum, p) => {
      return p > 0 ? sum + (p * Math.log(p)) : sum;
    }, 0);
  },

  argmax(array) {
    return array.reduce((iMax, x, i, arr) => x > arr[iMax] ? i : iMax, 0);
  },

  shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }
};