'use strict';

// 2401. Longest Nice Subarray: maintain a sliding window with disjoint set bits.
// O(n) time and O(1) auxiliary space for values below 2^30; inputs are read-only.
function solve(nums) {
  let mask = 0;
  let left = 0;
  let answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    while (mask & nums[right]) {
      // Disjoint bits in the valid window make XOR an exact removal.
      mask ^= nums[left];
      left += 1;
    }
    mask |= nums[right];
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

const longestNiceSubarray = solve;
class Solution {
  longestNiceSubarray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestNiceSubarray };
