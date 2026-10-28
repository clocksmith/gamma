'use strict';

// 318. Maximum Product of Word Lengths (Medium).
// Specification: https://leetcode.com/problems/maximum-product-of-word-lengths/description/
function maskOf(word) {
  let mask = 0;
  for (const ch of word) mask |= 1 << (ch.charCodeAt(0) - 97);
  return mask;
}
function solve(words) {
  const masks = words.map(maskOf);
  let best = 0;
  for (let i = 0; i < words.length; i++) {
    for (let j = i + 1; j < words.length; j++) {
      if ((masks[i] & masks[j]) === 0) best = Math.max(best, words[i].length * words[j].length);
    }
  }
  return best;
}
const maxProduct = solve;
class Solution { maxProduct(words) { return solve(words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
