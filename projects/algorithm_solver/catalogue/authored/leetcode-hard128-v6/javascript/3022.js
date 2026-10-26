'use strict';

// 3022. Minimize OR of Remaining Elements Using Operations.
// Greedily forbid bits and count zero-AND segments for each candidate mask; O(30*n) time, O(1) space. Inputs are preserved.

function solve(nums, k) {
  let forbidden = 0, answer = 0;
  for (let bit = 29; bit >= 0; bit -= 1) {
    const candidate = forbidden | (1 << bit);
    let current = (1 << 30) - 1, segments = 0;
    for (const value of nums) {
      current &= value;
      if ((current & candidate) === 0) { segments += 1; current = (1 << 30) - 1; }
    }
    if (nums.length - segments <= k) forbidden = candidate;
    else answer |= 1 << bit;
  }
  return answer;
}

const minOrAfterOperations = solve;
class Solution {
  minOrAfterOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOrAfterOperations };
