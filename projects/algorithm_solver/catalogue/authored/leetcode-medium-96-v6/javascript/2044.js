'use strict';

// 2044. Count Number of Maximum Bitwise-OR Subsets: enumerate inclusion choices while carrying their accumulated bitwise OR.
// O(2^n) time and O(n) auxiliary stack space; inputs are read-only.
function solve(nums) {
  let target = 0;
  for (const value of nums) target |= value;
  function count(index, value) {
    if (index === nums.length) return value === target ? 1 : 0;
    return count(index + 1, value) + count(index + 1, value | nums[index]);
  }
  return count(0, 0) - (target === 0 ? 1 : 0);
}

const countMaxOrSubsets = solve;
class Solution {
  countMaxOrSubsets(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countMaxOrSubsets };
