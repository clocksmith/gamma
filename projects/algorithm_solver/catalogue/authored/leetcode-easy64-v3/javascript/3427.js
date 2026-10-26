'use strict';

// 3427. Sum of Variable Length Subarrays (Easy).
// Specification: https://leetcode.com/problems/sum-of-variable-length-subarrays/description/
// O(n) time and space; prefix sums evaluate the subarray ending at every index.
function solve(nums) {
  const prefix = [0];
  let total = 0;
  for (let index = 0; index < nums.length; index++) {
    prefix.push(prefix[index] + nums[index]);
    const start = Math.max(0, index - nums[index]);
    total += prefix[index + 1] - prefix[start];
  }
  return total;
}

const subarraySum = solve;
class Solution {
  subarraySum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subarraySum };
