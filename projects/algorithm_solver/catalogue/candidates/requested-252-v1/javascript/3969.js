/**
 * 3969. Valid Subarrays With Matching Sum Digits I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/valid-subarrays-with-matching-sum-digits-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3969.Valid%20Subarrays%20With%20Matching%20Sum%20Digits%20I/README_EN.md
 * Complexity: O(n^2 + n log(sum(nums))) time, O(1) space.
 * Positive values make the decimal power monotone for each left endpoint. n <= 1500 and sum <= 1.5e12, exact Number arithmetic. Inputs preserved.
 */

function solve(nums, x) {
  let answer = 0;
  for (let left = 0; left < nums.length; left++) {
    let total = 0;
    let power = 1;
    for (let right = left; right < nums.length; right++) {
      total += nums[right];
      while (total >= power * 10) power *= 10;
      if (total % 10 === x && Math.floor(total / power) === x) answer++;
    }
  }
  return answer;
}

function countValidSubarrays(nums, x) {
  return solve(nums, x);
}

class Solution {
  countValidSubarrays(nums, x) {
    return solve(nums, x);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countValidSubarrays, Solution };
}
