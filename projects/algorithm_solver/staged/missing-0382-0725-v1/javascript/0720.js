'use strict';

// 720. Longest Word in Dictionary.

function solve(words) {
  const built = new Set(['']);
  let answer = '';
  for (const word of words.slice().sort()) {
    if (built.has(word.slice(0, -1))) {
      built.add(word); if (word.length > answer.length) answer = word;
    }
  }
  return answer;
}

const longestWord = solve;
class Solution {
  longestWord(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestWord };
