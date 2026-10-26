'use strict';

// 1502. Can Make Arithmetic Progression From Sequence (Easy).
// Specification: https://leetcode.com/problems/can-make-arithmetic-progression-from-sequence/description/
// O(n log n) time, O(n) space; sort a copy and preserve arr.
function solve(arr) {
  const ordered = arr.slice().sort((left, right) => left - right);
  const difference = ordered[1] - ordered[0];
  for (let index = 2; index < ordered.length; index++) {
    if (ordered[index] - ordered[index - 1] !== difference) return false;
  }
  return true;
}

const canMakeArithmeticProgression = solve;
class Solution {
  canMakeArithmeticProgression(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canMakeArithmeticProgression };
