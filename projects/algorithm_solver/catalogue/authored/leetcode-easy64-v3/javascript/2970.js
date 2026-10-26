'use strict';

// 2970. Count the Number of Incremovable Subarrays I (Easy).
// Specification: https://leetcode.com/problems/count-the-number-of-incremovable-subarrays-i/description/
// O(n^2) time, O(n) space; prefix/suffix validity avoids copying each removal.
function solve(nums) {
  const count = nums.length;
  const prefix = new Array(count).fill(true);
  const suffix = new Array(count).fill(true);
  for (let index = 1; index < count; index++) {
    prefix[index] = prefix[index - 1] && nums[index - 1] < nums[index];
  }
  for (let index = count - 2; index >= 0; index--) {
    suffix[index] = suffix[index + 1] && nums[index] < nums[index + 1];
  }
  let result = 0;
  for (let left = 0; left < count; left++) {
    if (left > 0 && !prefix[left - 1]) continue;
    for (let right = left; right < count; right++) {
      if (right + 1 < count && !suffix[right + 1]) continue;
      if (left > 0 && right + 1 < count && nums[left - 1] >= nums[right + 1]) continue;
      result++;
    }
  }
  return result;
}

const incremovableSubarrayCount = solve;
class Solution {
  incremovableSubarrayCount(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, incremovableSubarrayCount };
