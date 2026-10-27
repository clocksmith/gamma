'use strict';
// 244. Shortest Word Distance II.
class WordDistance {
  constructor(wordsDict) {
    this.positions = new Map();
    wordsDict.forEach((word, index) => {
      if (!this.positions.has(word)) this.positions.set(word, []);
      this.positions.get(word).push(index);
    });
  }
  shortest(word1, word2) {
    const left = this.positions.get(word1); const right = this.positions.get(word2);
    let i = 0; let j = 0; let best = Infinity;
    while (i < left.length && j < right.length) {
      best = Math.min(best, Math.abs(left[i] - right[j]));
      if (left[i] < right[j]) i += 1; else j += 1;
    }
    return best;
  }
}
function solve(wordsDict, queries) {
  const distance = new WordDistance(wordsDict);
  return queries.map(query => distance.shortest(...query));
}
if (typeof module !== 'undefined') module.exports = { solve, WordDistance };
