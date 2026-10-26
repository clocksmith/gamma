'use strict';

// 3304. Find the K-th Character in String Game I (Easy).
// Specification: https://leetcode.com/problems/find-the-k-th-character-in-string-game-i/description/
// O(log k) time, O(1) space; each set bit of k - 1 contributes one alphabet step.
function solve(k) {
  let index = k - 1;
  let shifts = 0;
  while (index > 0) {
    shifts += index % 2;
    index = Math.floor(index / 2);
  }
  return String.fromCharCode(97 + shifts % 26);
}

const kthCharacter = solve;
class Solution {
  kthCharacter(k) { return solve(k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthCharacter };
