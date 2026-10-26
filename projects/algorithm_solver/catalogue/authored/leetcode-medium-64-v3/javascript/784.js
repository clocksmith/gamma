'use strict';

// 784. Letter Case Permutation: expand lowercase and uppercase choices for each ASCII letter.
// O(n * 2^l) time and output space for l letters; inputs are read-only.
function solve(s) {
  let variants = [''];
  for (const char of s) {
    const next = [];
    const choices = char >= '0' && char <= '9' ? [char] : [char.toLowerCase(), char.toUpperCase()];
    for (const prefix of variants) {
      for (const choice of choices) next.push(prefix + choice);
    }
    variants = next;
  }
  return variants;
}

const letterCasePermutation = solve;
class Solution {
  letterCasePermutation(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, letterCasePermutation };
