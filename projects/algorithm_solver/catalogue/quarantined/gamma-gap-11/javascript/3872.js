'use strict';

// 3872. Longest Arithmetic Sequence After Changing At Most One Element.
// O(n) time and space; join equal-difference runs through an integer replacement or extend one run.
function solve(nums) {
  const n = nums.length;
  const left = Array(n).fill(1);
  const right = Array(n).fill(1);
  let answer = 1;
  for (let index = 1; index < n; index += 1) {
    left[index] = index > 1 && nums[index] - nums[index - 1] === nums[index - 1] - nums[index - 2] ? left[index - 1] + 1 : 2;
    answer = Math.max(answer, left[index]);
  }
  for (let index = n - 2; index >= 0; index -= 1) {
    right[index] = index + 2 < n && nums[index + 1] - nums[index] === nums[index + 2] - nums[index + 1] ? right[index + 1] + 1 : 2;
  }
  for (let index = 0; index < n; index += 1) {
    if (index > 0) answer = Math.max(answer, left[index - 1] + 1);
    if (index + 1 < n) answer = Math.max(answer, right[index + 1] + 1);
    if (index > 0 && index + 1 < n && (nums[index + 1] - nums[index - 1]) % 2 === 0) {
      const difference = (nums[index + 1] - nums[index - 1]) / 2;
      const before = index > 1 && nums[index - 1] - nums[index - 2] === difference ? left[index - 1] : 1;
      const after = index + 2 < n && nums[index + 2] - nums[index + 1] === difference ? right[index + 1] : 1;
      answer = Math.max(answer, before + 1 + after);
    }
  }
  return answer;
}

const longestArithmetic = solve;
class Solution {
  longestArithmetic(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestArithmetic };
