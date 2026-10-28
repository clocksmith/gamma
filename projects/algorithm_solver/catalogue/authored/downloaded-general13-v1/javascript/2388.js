'use strict';

// 2388. Replace Elements in an Array (Medium).
// Specification: https://leetcode.com/problems/replace-elements-in-an-array/description/
function solve(nums, operations) {
  const pos = new Map();
  nums.forEach((v, i) => pos.set(v, i));
  for (const [a, b] of operations) {
    const idx = pos.get(a);
    nums[idx] = b;
    pos.delete(a);
    pos.set(b, idx);
  }
  return nums;
}
const arrayChange = solve;
class Solution { arrayChange(nums, operations) { return solve(nums, operations); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrayChange };
