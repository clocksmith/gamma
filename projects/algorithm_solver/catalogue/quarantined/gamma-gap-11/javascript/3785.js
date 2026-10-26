'use strict';

// 3785. Minimum Swaps to Avoid Forbidden Values.
// O(n) expected time and O(n) space; feasibility is checked before the dominant-conflict bound.
function solve(nums, forbidden) {
  const n = nums.length;
  const combined = new Map();
  for (let index = 0; index < n; index += 1) {
    combined.set(nums[index], (combined.get(nums[index]) || 0) + 1);
    combined.set(forbidden[index], (combined.get(forbidden[index]) || 0) + 1);
  }
  for (const count of combined.values()) if (count > n) return -1;
  const bad = new Map();
  let total = 0;
  let largest = 0;
  for (let index = 0; index < n; index += 1) {
    if (nums[index] !== forbidden[index]) continue;
    total += 1;
    const count = (bad.get(nums[index]) || 0) + 1;
    bad.set(nums[index], count);
    largest = Math.max(largest, count);
  }
  return Math.max(Math.floor((total + 1) / 2), largest);
}

const minSwaps = solve;
class Solution {
  minSwaps(nums, forbidden) { return solve(nums, forbidden); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSwaps };
