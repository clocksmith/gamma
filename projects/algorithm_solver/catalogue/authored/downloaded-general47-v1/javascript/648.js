'use strict';

// 648. Replace Words (Medium).
// Specification: https://leetcode.com/problems/replace-words/description/
function solve(dictionary, sentence) {
  const roots = new Set(dictionary);
  const result = [];
  for (const word of sentence.split(' ')) {
    let replacement = word;
    for (let length = 1; length <= word.length; length++) {
      const prefix = word.slice(0, length);
      if (roots.has(prefix)) { replacement = prefix; break; }
    }
    result.push(replacement);
  }
  return result.join(' ');
}
const replaceWords = solve;
class Solution { replaceWords(dictionary, sentence) { return solve(dictionary, sentence); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, replaceWords };
