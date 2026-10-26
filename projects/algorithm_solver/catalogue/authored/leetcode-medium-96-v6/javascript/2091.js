'use strict';

// 2091. Removing Minimum and Maximum From Array: compare removing both extremes from either end or splitting the removals.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let smallest = 0;
  let largest = 0;
  for (let index = 0; index < nums.length; index += 1) {
    if (nums[index] < nums[smallest]) smallest = index;
    if (nums[index] > nums[largest]) largest = index;
  }
  const left = Math.min(smallest, largest);
  const right = Math.max(smallest, largest);
  return Math.min(right + 1, nums.length - left, left + 1 + nums.length - right);
}

const minimumDeletions = solve;
class Solution {
  minimumDeletions(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDeletions };
