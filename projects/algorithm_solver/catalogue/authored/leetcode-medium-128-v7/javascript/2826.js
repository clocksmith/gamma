'use strict';

// 2826. Sorting Three Groups: maintain minimal corrections for prefixes ending in each of the three ordered groups.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let first = 0;
  let second = 0;
  let third = 0;
  for (const value of nums) {
    const nextFirst = first + Number(value !== 1);
    const nextSecond = Math.min(first, second) + Number(value !== 2);
    const nextThird = Math.min(first, second, third) + Number(value !== 3);
    first = nextFirst;
    second = nextSecond;
    third = nextThird;
  }
  return Math.min(first, second, third);
}

const minimumOperations = solve;
class Solution {
  minimumOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
