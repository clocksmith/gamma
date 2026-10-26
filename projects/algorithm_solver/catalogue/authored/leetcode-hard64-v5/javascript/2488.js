'use strict';

// 2488. Count Subarrays With Median K. Combine signed balances on both sides of the unique median; O(n) time and O(n) space. Inputs are preserved.

function solve(nums, k) {
  const pivot = nums.indexOf(k);
  const counts = new Map([[0, 1]]);
  let balance = 0;
  for (let index = pivot + 1; index < nums.length; index += 1) {
    balance += nums[index] > k ? 1 : -1;
    counts.set(balance, (counts.get(balance) || 0) + 1);
  }
  let answer = (counts.get(0) || 0) + (counts.get(1) || 0);
  balance = 0;
  for (let index = pivot - 1; index >= 0; index -= 1) {
    balance += nums[index] > k ? 1 : -1;
    answer += (counts.get(-balance) || 0) + (counts.get(1 - balance) || 0);
  }
  return answer;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
