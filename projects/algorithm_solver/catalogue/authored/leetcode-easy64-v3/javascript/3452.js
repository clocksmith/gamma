'use strict';

// 3452. Sum of Good Numbers (Easy).
// Specification: https://leetcode.com/problems/sum-of-good-numbers/description/
// O(n) time, O(1) space; compare only existing neighbors at distance k.
function solve(nums, k) {
  let total = 0;
  for (let index = 0; index < nums.length; index++) {
    if (index >= k && nums[index] <= nums[index - k]) continue;
    if (index + k < nums.length && nums[index] <= nums[index + k]) continue;
    total += nums[index];
  }
  return total;
}

const sumOfGoodNumbers = solve;
class Solution {
  sumOfGoodNumbers(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfGoodNumbers };
