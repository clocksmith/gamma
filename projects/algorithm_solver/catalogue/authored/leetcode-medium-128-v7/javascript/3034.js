'use strict';

// 3034. Number of Subarrays That Match a Pattern I: check each candidate window against its required adjacent comparison signs.
// O(n * m) time and O(1) auxiliary space, where m is the pattern length; inputs are read-only.
function solve(nums, pattern) {
  let total = 0;
  for (let start = 0; start + pattern.length < nums.length; start += 1) {
    let matches = true;
    for (let offset = 0; offset < pattern.length; offset += 1) {
      const left = nums[start + offset];
      const right = nums[start + offset + 1];
      const observed = Number(right > left) - Number(right < left);
      if (observed !== pattern[offset]) {
        matches = false;
        break;
      }
    }
    if (matches) total += 1;
  }
  return total;
}

const countMatchingSubarrays = solve;
class Solution {
  countMatchingSubarrays(nums, pattern) { return solve(nums, pattern); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countMatchingSubarrays };
