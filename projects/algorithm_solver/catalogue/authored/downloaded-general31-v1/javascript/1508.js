'use strict';

// 1508. Range Sum of Sorted Subarray Sums (Medium).
// Specification: https://leetcode.com/problems/range-sum-of-sorted-subarray-sums/description/
function solve(nums, n, left, right) {
  const MOD = 1000000007;
  const sums = [];
  for (let start = 0; start < nums.length; start++) {
    let total = 0;
    for (let end = start; end < nums.length; end++) { total += nums[end]; sums.push(total); }
  }
  sums.sort((a, b) => a - b);
  let answer = 0;
  for (let i = left - 1; i < right; i++) answer = (answer + sums[i]) % MOD;
  return answer;
}
const rangeSum = solve;
class Solution { rangeSum(nums, n, left, right) { return solve(nums, n, left, right); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rangeSum };
