'use strict';

// 3649. Number of Perfect Pairs.
// Specification: https://leetcode.com/problems/number-of-perfect-pairs/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n log n) time, O(n) space; conditions reduce to max(abs(a),abs(b)) <= 2 * min(abs(a),abs(b)).
// Inputs are not modified.

function solve(nums) {
  const values = nums.map(Math.abs).sort((a, b) => a - b);
  let left = 0, answer = 0;
  for (let right = 0; right < values.length; right++) {
    while (2 * values[left] < values[right]) left++;
    answer += right - left;
  }
  return answer;
}

const perfectPairs = solve;
class Solution {
  perfectPairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, perfectPairs };
