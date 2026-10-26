'use strict';

// 1787. Make the XOR of All Segments Equal to Zero.
// DP over 1024 XOR states and residue-class value counts; O(1024*(n+k)) time, O(n+1024) space. Inputs are preserved.

function solve(nums, k) {
  let costs = Array(1024).fill(nums.length);
  costs[0] = 0;
  for (let residue = 0; residue < k; residue += 1) {
    const counts = new Map();
    let size = 0;
    for (let i = residue; i < nums.length; i += k) { counts.set(nums[i], (counts.get(nums[i]) || 0) + 1); size += 1; }
    let minimum = Infinity;
    for (const value of costs) minimum = Math.min(minimum, value);
    const following = Array(1024).fill(minimum + size);
    for (const [value, count] of counts) {
      for (let target = 0; target < 1024; target += 1) following[target] = Math.min(following[target], costs[target ^ value] + size - count);
    }
    costs = following;
  }
  return costs[0];
}

const minChanges = solve;
class Solution {
  minChanges(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minChanges };
