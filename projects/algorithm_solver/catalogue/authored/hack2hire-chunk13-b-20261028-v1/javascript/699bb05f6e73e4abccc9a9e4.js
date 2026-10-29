"use strict";
// Hack2Hire 699bb05f6e73e4abccc9a9e4 (Sentence Variations with Anagram) over an INFERRED spec; qualification unknown.

function signature(word) { return word.split("").sort().join(""); }

function solve(wordSet, sentences) {
  const groups = new Map();
  for (const word of wordSet) {
    const key = signature(word);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(word);
  }
  for (const group of groups.values()) group.sort();
  const options = new Map();
  const choices = (word) => {
    if (!options.has(word)) {
      const group = groups.get(signature(word)) || [];
      options.set(word, group.includes(word) ? group : [...group, word].sort());
    }
    return options.get(word);
  };
  return sentences.map((sentence) => {
    let partial = null;
    for (const word of sentence.split(" ")) {
      const opts = choices(word);
      if (partial === null) partial = opts.slice();
      else {
        const next = [];
        for (const p of partial) for (const o of opts) next.push(p + " " + o);
        partial = next;
      }
    }
    return partial;
  });
}

function sentenceVariations(wordSet, sentences) { return solve(wordSet, sentences); }

module.exports = solve;
module.exports.sentenceVariations = sentenceVariations;
