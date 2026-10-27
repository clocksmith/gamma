'use strict';

// 648. Replace Words.

function solve(dictionary, sentence) {
  const trie = new Map();
  for (const root of dictionary) {
    let node = trie;
    for (const char of root) { if (!node.has(char)) node.set(char, new Map()); node = node.get(char); }
    node.set('', true);
  }
  return sentence.split(' ').map(word => {
    let node = trie;
    for (let i = 0; i < word.length; i += 1) {
      if (!node.has(word[i])) break;
      node = node.get(word[i]);
      if (node.has('')) return word.slice(0, i + 1);
    }
    return word;
  }).join(' ');
}

const replaceWords = solve;
class Solution {
  replaceWords(dictionary, sentence) { return solve(dictionary, sentence); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, replaceWords };
