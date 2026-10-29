"use strict";
// Hack2Hire 688bd5423867670cfb894188 (Detect Abusive Words) over an INFERRED spec; qualification unknown.

function solve(words, substitutions, comment) {
  const children = [new Map()];
  const ends = [false];
  for (const word of words) {
    let node = 0;
    for (const ch of word) {
      let next = children[node].get(ch);
      if (next === undefined) {
        next = children.length;
        children[node].set(ch, next);
        children.push(new Map());
        ends.push(false);
      }
      node = next;
    }
    ends[node] = true;
  }
  const letters = new Map();
  for (const [symbol, letter] of substitutions) {
    if (!letters.has(symbol)) letters.set(symbol, []);
    const options = letters.get(symbol);
    if (!options.includes(letter)) options.push(letter);
  }
  const found = [];
  const tokens = comment.split(" ");
  for (let index = 0; index < tokens.length; index++) {
    // trie nodes have one parent each, so distinct steps never reach the same node twice
    let current = [0];
    for (const ch of tokens[index]) {
      const options = ch >= "a" && ch <= "z" ? [ch] : (letters.get(ch) || []);
      const following = [];
      for (const node of current) {
        const edges = children[node];
        for (const letter of options) {
          const next = edges.get(letter);
          if (next !== undefined) following.push(next);
        }
      }
      current = following;
      if (current.length === 0) break;
    }
    if (current.some((node) => ends[node])) found.push(index);
  }
  return found;
}

function detectAbusiveWords(words, substitutions, comment) { return solve(words, substitutions, comment); }

module.exports = solve;
module.exports.detectAbusiveWords = detectAbusiveWords;
