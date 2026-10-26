'use strict';

// 3174. Clear Digits (Easy).
// Specification: https://leetcode.com/problems/clear-digits/description/
// O(n) time and space; a stack removes the closest surviving letter on the left.
function solve(s) {
  const letters = [];
  for (const character of s) {
    if (character >= '0' && character <= '9') letters.pop();
    else letters.push(character);
  }
  return letters.join('');
}

const clearDigits = solve;
class Solution {
  clearDigits(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, clearDigits };
