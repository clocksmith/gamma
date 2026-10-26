'use strict';

// 1671. Minimum Number of Removals to Make Mountain Array: strict LIS lengths in both directions; O(n log n) time and O(n) space.

function solve(nums) {
  function lengths(reverse) {
    const tails = [];
    const answer = Array(nums.length).fill(0);
    for (let offset = 0; offset < nums.length; offset += 1) {
      const index = reverse ? nums.length - 1 - offset : offset;
      const value = nums[index];
      let left = 0;
      let right = tails.length;
      while (left < right) {
        const middle = Math.floor((left + right) / 2);
        if (tails[middle] < value) left = middle + 1;
        else right = middle;
      }
      tails[left] = value;
      answer[index] = left + 1;
    }
    return answer;
  }
  const increasing = lengths(false);
  const decreasing = lengths(true);
  let longest = 0;
  for (let index = 0; index < nums.length; index += 1) {
    if (increasing[index] > 1 && decreasing[index] > 1) longest = Math.max(longest, increasing[index] + decreasing[index] - 1);
  }
  return nums.length - longest;
}

const minimumMountainRemovals = solve;
class Solution {
  minimumMountainRemovals(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumMountainRemovals };
