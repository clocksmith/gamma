'use strict';

// 189. Rotate Array (Medium).
// Specification: https://leetcode.com/problems/rotate-array/description/
function solve(nums, k) {
  const n = nums.length;
  if (n === 0) return [];
  const steps = ((k % n) + n) % n;
  return nums.slice(n - steps).concat(nums.slice(0, n - steps));
}
const rotate = solve;
class Solution { rotate(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotate };
