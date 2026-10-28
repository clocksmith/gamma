'use strict';

// 820. Short Encoding of Words (Medium).
// Specification: https://leetcode.com/problems/short-encoding-of-words/description/
function solve(words) {
  const unique = new Set(words);
  for (const word of words) {
    for (let i = 1; i < word.length; i++) unique.delete(word.slice(i));
  }
  let total = 0;
  for (const word of unique) total += word.length + 1;
  return total;
}
const minimumLengthEncoding = solve;
class Solution { minimumLengthEncoding(words) { return solve(words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumLengthEncoding };
