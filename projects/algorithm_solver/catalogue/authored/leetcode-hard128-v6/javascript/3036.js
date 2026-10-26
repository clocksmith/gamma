'use strict';

// 3036. Number of Subarrays That Match a Pattern II.
// KMP over adjacent comparison signs; O(n+m) time, O(m) space. Inputs are preserved.

function solve(nums, pattern) {
  const border = Array(pattern.length).fill(0);
  for (let index = 1; index < pattern.length; index += 1) {
    let length = border[index - 1];
    while (length > 0 && pattern[index] !== pattern[length]) length = border[length - 1];
    border[index] = length + Number(pattern[index] === pattern[length]);
  }
  let answer = 0, length = 0;
  for (let index = 1; index < nums.length; index += 1) {
    const comparison = Number(nums[index] > nums[index - 1]) - Number(nums[index] < nums[index - 1]);
    while (length > 0 && comparison !== pattern[length]) length = border[length - 1];
    if (comparison === pattern[length]) length += 1;
    if (length === pattern.length) { answer += 1; length = border[length - 1]; }
  }
  return answer;
}

const countMatchingSubarrays = solve;
class Solution {
  countMatchingSubarrays(nums, pattern) { return solve(nums, pattern); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countMatchingSubarrays };
