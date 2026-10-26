'use strict';

// 1283. Find the Smallest Divisor Given a Threshold: binary search the first divisor whose rounded sum fits.
// O(n log M) time and O(1) auxiliary space for maximum value M; inputs are read-only.
function solve(nums, threshold) {
  let low = 1;
  let high = 1;
  for (const value of nums) high = Math.max(high, value);
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let total = 0;
    for (const value of nums) {
      total += Math.floor((value + middle - 1) / middle);
      if (total > threshold) break;
    }
    if (total <= threshold) high = middle;
    else low = middle + 1;
  }
  return low;
}

const smallestDivisor = solve;
class Solution {
  smallestDivisor(nums, threshold) { return solve(nums, threshold); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestDivisor };
