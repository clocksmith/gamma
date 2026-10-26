'use strict';

// 266. Palindrome Permutation (Easy).
// Specification: https://leetcode.com/problems/palindrome-permutation/description/
// O(n) expected time, O(a) space for distinct characters; at most one odd count.
function solve(s) {
  const odd = new Set();
  for (const character of s) {
    if (odd.has(character)) odd.delete(character);
    else odd.add(character);
  }
  return odd.size <= 1;
}

const canPermutePalindrome = solve;
class Solution {
  canPermutePalindrome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canPermutePalindrome };
