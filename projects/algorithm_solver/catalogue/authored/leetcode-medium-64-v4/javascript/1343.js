'use strict';

// 1343. Number of Sub-arrays of Size K and Average Greater than or Equal to Threshold: compare sliding-window sums without floating-point averages.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(arr, k, threshold) {
  let total = 0;
  let count = 0;
  const required = k * threshold;
  for (let index = 0; index < arr.length; index += 1) {
    total += arr[index];
    if (index >= k) total -= arr[index - k];
    if (index + 1 >= k && total >= required) count += 1;
  }
  return count;
}

const numOfSubarrays = solve;
class Solution {
  numOfSubarrays(arr, k, threshold) { return solve(arr, k, threshold); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfSubarrays };
