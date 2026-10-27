'use strict';

// 676. Implement Magic Dictionary.

class MagicDictionary {
  constructor() { this.patterns = new Map(); }
  buildDict(dictionary) {
    this.patterns.clear();
    for (const word of dictionary) for (let i = 0; i < word.length; i += 1) {
      const pattern = word.slice(0, i) + '*' + word.slice(i + 1);
      if (!this.patterns.has(pattern)) this.patterns.set(pattern, new Set());
      this.patterns.get(pattern).add(word[i]);
    }
  }
  search(searchWord) {
    for (let i = 0; i < searchWord.length; i += 1) {
      const pattern = searchWord.slice(0, i) + '*' + searchWord.slice(i + 1), values = this.patterns.get(pattern);
      if (values && (values.size > 1 || !values.has(searchWord[i]))) return true;
    }
    return false;
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MagicDictionary(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MagicDictionary;

if (typeof module !== 'undefined') module.exports = { solve, MagicDictionary, Solution };
