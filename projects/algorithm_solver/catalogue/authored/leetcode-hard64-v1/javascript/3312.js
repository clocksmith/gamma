'use strict';

// 3312. Sorted GCD Pair Queries: count exact gcds by subtracting proper multiples.
// O(n + M log M + q log M) time and O(M + q) space. Inputs are preserved.
function solve(nums, queries) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const frequency = new Int32Array(maximum + 1);
  for (const value of nums) frequency[value] += 1;
  // Pair counts can exceed int32 but are exact JavaScript Numbers.
  const exact = new Float64Array(maximum + 1);
  for (let divisor = maximum; divisor > 0; divisor -= 1) {
    let count = 0;
    for (let multiple = divisor; multiple <= maximum; multiple += divisor) count += frequency[multiple];
    exact[divisor] = count * (count - 1) / 2;
    for (let multiple = 2 * divisor; multiple <= maximum; multiple += divisor) exact[divisor] -= exact[multiple];
  }
  for (let divisor = 1; divisor <= maximum; divisor += 1) exact[divisor] += exact[divisor - 1];
  return queries.map(rank => {
    let left = 1;
    let right = maximum;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (exact[middle] <= rank) left = middle + 1;
      else right = middle;
    }
    return left;
  });
}

const gcdValues = solve;
class Solution {
  gcdValues(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gcdValues };
