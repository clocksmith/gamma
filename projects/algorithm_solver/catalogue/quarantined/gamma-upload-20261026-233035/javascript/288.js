'use strict';
// 288. Unique Word Abbreviation.
function abbreviation(word) { return word.length <= 2 ? word : `${word[0]}${word.length - 2}${word[word.length - 1]}`; }
class ValidWordAbbr {
  constructor(dictionary) {
    this.words = new Map();
    for (const word of dictionary) {
      const key = abbreviation(word);
      if (!this.words.has(key)) this.words.set(key, new Set());
      this.words.get(key).add(word);
    }
  }
  isUnique(word) {
    const values = this.words.get(abbreviation(word));
    return values === undefined || (values.size === 1 && values.has(word));
  }
}
function solve(dictionary, queries) {
  const structure = new ValidWordAbbr(dictionary);
  return queries.map(word => structure.isUnique(word));
}
if (typeof module !== 'undefined') module.exports = { solve, ValidWordAbbr };
