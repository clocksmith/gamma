'use strict';

// 1300. Sum of Mutated Array Closest to Target: binary search the cap then compare its two neighboring sums.
// O(n log(M + 1)) time and O(1) auxiliary space, where M is the largest value; inputs are read-only.
function solve(arr, target) {
  let low = 0;
  let high = 0;
  for (const value of arr) high = Math.max(high, value);
  function cappedSum(cap) {
    let total = 0;
    for (const value of arr) total += Math.min(value, cap);
    return total;
  }
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (cappedSum(middle) < target) low = middle + 1;
    else high = middle;
  }
  if (low === 0) return 0;
  return Math.abs(cappedSum(low - 1) - target) <= Math.abs(cappedSum(low) - target) ? low - 1 : low;
}

const findBestValue = solve;
class Solution {
  findBestValue(arr, target) { return solve(arr, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findBestValue };
