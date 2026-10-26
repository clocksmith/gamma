'use strict';

// 1832. Check if the Sentence Is Pangram (Easy).
// Specification: https://leetcode.com/problems/check-if-the-sentence-is-pangram/description/
// O(n) time, O(1) alphabet space; the input uses lowercase ASCII letters.
function solve(sentence) {
  return new Set(sentence).size === 26;
}

const checkIfPangram = solve;
class Solution {
  checkIfPangram(sentence) { return solve(sentence); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkIfPangram };
