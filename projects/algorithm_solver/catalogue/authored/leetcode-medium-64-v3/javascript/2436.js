'use strict';

// 2436. Minimum Split Into Subarrays With GCD Greater Than One: extend each part until its running gcd would become one.
// O(n log M) time and O(1) auxiliary space for maximum value M; inputs are read-only.
function solve(nums) {
  function gcd(left, right) {
    while (right !== 0) [left, right] = [right, left % right];
    return left;
  }
  let parts = 1;
  let current = 0;
  for (const value of nums) {
    const merged = gcd(current, value);
    if (merged === 1) {
      parts += 1;
      current = value;
    } else current = merged;
  }
  return parts;
}

const minimumSplits = solve;
class Solution {
  minimumSplits(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSplits };
