'use strict';

// 2295. Replace Elements in an Array (Medium).
// Specification: https://leetcode.com/problems/replace-elements-in-an-array/description/
function solve(nums, operations) {
  const pos = new Map();
  nums.forEach((v, i) => pos.set(v, i));
  const out = nums.slice();
  for (const op of operations) {
    const idx = pos.get(op[0]);
    out[idx] = op[1];
    pos.delete(op[0]);
    pos.set(op[1], idx);
  }
  return out;
}
const arrayChange = solve;
class Solution { arrayChange(nums, operations) { return solve(nums, operations); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrayChange };
