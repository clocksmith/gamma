class Solution {
  areSentencesSimilar(sentence1, sentence2, similarPairs) {
    if (sentence1.length !== sentence2.length) {
      return false;
    }

    const neighbors = new Map();
    for (const [left, right] of similarPairs) {
      if (!neighbors.has(left)) {
        neighbors.set(left, new Set());
      }
      if (!neighbors.has(right)) {
        neighbors.set(right, new Set());
      }
      neighbors.get(left).add(right);
      neighbors.get(right).add(left);
    }
    for (let index = 0; index < sentence1.length; index += 1) {
      const left = sentence1[index];
      const right = sentence2[index];
      if (left === right) {
        continue;
      }
      if (!neighbors.has(left) || !neighbors.get(left).has(right)) {
        return false;
      }
    }
    return true;
  }
}
