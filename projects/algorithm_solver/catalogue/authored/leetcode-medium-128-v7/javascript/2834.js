'use strict';

// 2834. Find the Minimum Possible Sum of a Beautiful Array: sum the allowed lower half and the remaining consecutive values starting at target.
// O(1) arithmetic operations and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n, target) {
  const count = BigInt(n);
  const bound = BigInt(target);
  const small = count < bound / 2n ? count : bound / 2n;
  const remaining = count - small;
  const total = small * (small + 1n) / 2n + remaining * (2n * bound + remaining - 1n) / 2n;
  return Number(total % 1000000007n);
}

const minimumPossibleSum = solve;
class Solution {
  minimumPossibleSum(n, target) { return solve(n, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumPossibleSum };
