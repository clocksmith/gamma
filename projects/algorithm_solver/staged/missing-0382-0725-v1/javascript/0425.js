'use strict';

// 425. Word Squares. Backtrack only through words having the required column prefix.

function solve(words) {
  if (words.length === 0) return [];
  const size = words[0].length, prefixes = new Map();
  for (const word of words) {
    for (let end = 0; end <= size; end += 1) {
      const prefix = word.slice(0, end);
      if (!prefixes.has(prefix)) prefixes.set(prefix, []);
      prefixes.get(prefix).push(word);
    }
  }
  const answer = [], square = [];
  function extend() {
    const row = square.length;
    if (row === size) { answer.push(square.slice()); return; }
    const prefix = square.map(word => word[row]).join('');
    for (const word of prefixes.get(prefix) || []) {
      square.push(word); extend(); square.pop();
    }
  }
  extend();
  return answer;
}

const wordSquares = solve;
class Solution {
  wordSquares(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordSquares };
