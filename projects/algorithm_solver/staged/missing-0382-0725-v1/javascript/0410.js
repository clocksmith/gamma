'use strict';

// 410. Split Array Largest Sum. Binary search the maximum segment sum for nonnegative inputs.

function solve(nums, k) {
  let low = 0, high = 0;
  for (const value of nums) { low = Math.max(low, value); high += value; }
  while (low < high) {
    const limit = Math.floor((low + high) / 2);
    let parts = 1, subtotal = 0;
    for (const value of nums) {
      if (subtotal + value > limit) { parts += 1; subtotal = 0; }
      subtotal += value;
    }
    if (parts <= k) high = limit;
    else low = limit + 1;
  }
  return low;
}

const splitArray = solve;
class Solution {
  splitArray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitArray };
