"use strict";
// Hack2Hire 68bad975b5314dcd938cb9ff (Top 10 Words, variant 2 of 2) over an INFERRED spec; qualification unknown.

class WordFrequencyTracker {
  constructor() {
    this.counts = new Map();
    this.top = [];
  }

  better(a, b) {
    const ca = this.counts.get(a), cb = this.counts.get(b);
    return ca > cb || (ca === cb && a < b);
  }

  addText(text) {
    for (const match of text.match(/[A-Za-z]+/g) || []) {
      const word = match.toLowerCase();
      this.counts.set(word, (this.counts.get(word) || 0) + 1);
      const top = this.top;
      const at = top.indexOf(word);
      if (at >= 0) top.splice(at, 1);
      else if (top.length === 10 && !this.better(word, top[9])) continue;
      let i = top.length;
      while (i > 0 && this.better(word, top[i - 1])) i -= 1;
      top.splice(i, 0, word);
      if (top.length > 10) top.pop();
    }
  }

  getTop10() {
    return this.top.map((word) => [word, this.counts.get(word)]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "WordFrequencyTracker" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new WordFrequencyTracker(...argumentLists[0]);
  const allowed = new Set(["addText", "getTop10"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.WordFrequencyTracker = WordFrequencyTracker;
