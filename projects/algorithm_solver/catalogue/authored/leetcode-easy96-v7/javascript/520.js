'use strict';

// 520. Detect Capital (Easy).
// Specification: https://leetcode.com/problems/detect-capital/description/
// O(n) time, O(1) space; accept all lowercase, all uppercase, or just the first uppercase.
function solve(word) {
  let uppercase = 0;
  for (const character of word) {
    if (character >= 'A' && character <= 'Z') uppercase++;
  }
  return uppercase === 0 || uppercase === word.length ||
    (uppercase === 1 && word[0] >= 'A' && word[0] <= 'Z');
}

const detectCapitalUse = solve;
class Solution {
  detectCapitalUse(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, detectCapitalUse };
