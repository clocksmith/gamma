"use strict";

function solve(sentence1, sentence2, similarPairs) {
  if (sentence1.length !== sentence2.length) return false;
  const parent = new Map();
  function find(x) {
    let cur = x;
    while (parent.has(cur) && parent.get(cur) !== cur) {
      const p = parent.get(cur);
      const gp = parent.has(p) ? parent.get(p) : p;
      parent.set(cur, gp);
      cur = gp;
    }
    return cur;
  }
  for (let i = 0; i < similarPairs.length; i++) {
    const [a, b] = similarPairs[i];
    const ra = find(a), rb = find(b);
    if (ra !== rb) parent.set(ra, rb);
  }
  for (let i = 0; i < sentence1.length; i++) {
    if (sentence1[i] !== sentence2[i] && find(sentence1[i]) !== find(sentence2[i])) {
      return false;
    }
  }
  return true;
}

function areSentencesSimilarTwo(sentence1, sentence2, similarPairs) {
  return solve(sentence1, sentence2, similarPairs);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.areSentencesSimilarTwo = areSentencesSimilarTwo;
