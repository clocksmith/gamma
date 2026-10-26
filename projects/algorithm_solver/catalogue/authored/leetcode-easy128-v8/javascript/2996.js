'use strict';

// 2996. Smallest Missing Integer Greater Than Sequential Prefix Sum (Easy).
// Specification: https://leetcode.com/problems/smallest-missing-integer-greater-than-sequential-prefix-sum/description/
// O(n) expected time, O(n) space; start from the maximal sequential prefix sum and skip present values.
function solve(nums) {
  let candidate = nums[0];
  for (let index = 1; index < nums.length && nums[index] === nums[index - 1] + 1; index++) candidate += nums[index];
  const present = new Set(nums);
  while (present.has(candidate)) candidate++;
  return candidate;
}

const missingInteger = solve;
class Solution {
  missingInteger(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, missingInteger };
