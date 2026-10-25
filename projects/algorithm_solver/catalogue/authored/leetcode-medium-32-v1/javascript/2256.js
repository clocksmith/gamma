'use strict';

// 2256. Minimum Average Difference: compare prefix and suffix averages with earliest-index ties.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let total = 0;
  for (const value of nums) total += value;
  let prefix = 0;
  let bestDifference = Infinity;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    prefix += nums[index];
    const leftAverage = Math.floor(prefix / (index + 1));
    const remaining = nums.length - index - 1;
    const rightAverage = remaining > 0 ? Math.floor((total - prefix) / remaining) : 0;
    const difference = Math.abs(leftAverage - rightAverage);
    if (difference < bestDifference) {
      bestDifference = difference;
      answer = index;
    }
  }
  return answer;
}

const minimumAverageDifference = solve;
class Solution {
  minimumAverageDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumAverageDifference };
