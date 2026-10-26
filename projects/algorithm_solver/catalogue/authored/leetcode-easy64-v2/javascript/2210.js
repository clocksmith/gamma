'use strict';

// 2210. Count Hills and Valleys in an Array (Easy).
// Specification: https://leetcode.com/problems/count-hills-and-valleys-in-an-array/description/
// O(n) time, O(1) space; count each plateau once without changing nums.
function solve(nums) {
  let previous = nums[0];
  let result = 0;
  for (let index = 1; index < nums.length - 1; index++) {
    const current = nums[index];
    const following = nums[index + 1];
    if (current === following) continue;
    if ((current > previous && current > following) ||
        (current < previous && current < following)) result++;
    previous = current;
  }
  return result;
}

const countHillValley = solve;
class Solution {
  countHillValley(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countHillValley };
