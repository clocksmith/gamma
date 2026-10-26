'use strict';

// 2270. Number of Ways to Split Array: compare each proper prefix with the remaining suffix using one running sum.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let total = 0;
  for (const value of nums) total += value;
  let prefix = 0;
  let answer = 0;
  for (let index = 0; index + 1 < nums.length; index += 1) {
    prefix += nums[index];
    if (prefix >= total - prefix) answer += 1;
  }
  return answer;
}

const waysToSplitArray = solve;
class Solution {
  waysToSplitArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, waysToSplitArray };
