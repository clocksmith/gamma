'use strict';

// 3737. Count Subarrays With Majority Element I.
// O(n^2) time and O(1) auxiliary space for n <= 1000.
function solve(nums, target) {
  let answer = 0;
  for (let left = 0; left < nums.length; left += 1) {
    let balance = 0;
    for (let right = left; right < nums.length; right += 1) {
      balance += nums[right] === target ? 1 : -1;
      if (balance > 0) answer += 1;
    }
  }
  return answer;
}

const countMajoritySubarrays = solve;
class Solution {
  countMajoritySubarrays(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countMajoritySubarrays };
