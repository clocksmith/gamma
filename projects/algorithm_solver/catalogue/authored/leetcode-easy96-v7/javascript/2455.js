'use strict';

// 2455. Average Value of Even Numbers That Are Divisible by Three (Easy).
// Specification: https://leetcode.com/problems/average-value-of-even-numbers-that-are-divisible-by-three/description/
// O(n) time, O(1) space; average multiples of six and round down; preserve nums.
function solve(nums) {
  let total = 0;
  let count = 0;
  for (const value of nums) {
    if (value % 6 === 0) {
      total += value;
      count++;
    }
  }
  return count === 0 ? 0 : Math.floor(total / count);
}

const averageValue = solve;
class Solution {
  averageValue(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, averageValue };
