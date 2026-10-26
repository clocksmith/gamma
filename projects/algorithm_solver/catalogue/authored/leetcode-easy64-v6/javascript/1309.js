'use strict';

// 1309. Decrypt String from Alphabet to Integer Mapping (Easy).
// Specification: https://leetcode.com/problems/decrypt-string-from-alphabet-to-integer-mapping/description/
// O(n) time and space; consume valid one-digit or two-digit-hash tokens.
function solve(s) {
  const result = [];
  let index = 0;
  while (index < s.length) {
    const width = index + 2 < s.length && s[index + 2] === '#' ? 2 : 1;
    const value = Number(s.slice(index, index + width));
    result.push(String.fromCharCode(96 + value));
    index += width === 2 ? 3 : 1;
  }
  return result.join('');
}

const freqAlphabets = solve;
class Solution {
  freqAlphabets(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, freqAlphabets };
