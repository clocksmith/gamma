'use strict';

// 2411. Smallest Subarrays With Maximum Bitwise OR: scan backwards and retain the nearest occurrence of every possible set bit.
// O(30 * n) time and O(n) output space with O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  const nearest = new Array(30).fill(-1);
  const answer = new Array(nums.length).fill(1);
  for (let index = nums.length - 1; index >= 0; index -= 1) {
    let end = index;
    for (let bit = 0; bit < 30; bit += 1) {
      if (nums[index] & (1 << bit)) nearest[bit] = index;
      end = Math.max(end, nearest[bit]);
    }
    answer[index] = end - index + 1;
  }
  return answer;
}

const smallestSubarrays = solve;
class Solution {
  smallestSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestSubarrays };
