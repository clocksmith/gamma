'use strict';

// 3830. Longest Alternating Subarray After Removing At Most One Element.
// O(n) time and space; join compatible alternating runs across each possible removed element.
function solve(nums) {
  const n = nums.length;
  const signs = Array.from({ length: n - 1 }, (_, index) => Math.sign(nums[index + 1] - nums[index]));
  const left = Array(n).fill(1);
  const right = Array(n).fill(1);
  let answer = 1;
  for (let index = 1; index < n; index += 1) {
    if (signs[index - 1] !== 0) left[index] = index > 1 && signs[index - 2] === -signs[index - 1] ? left[index - 1] + 1 : 2;
    answer = Math.max(answer, left[index]);
  }
  for (let index = n - 2; index >= 0; index -= 1) {
    if (signs[index] !== 0) right[index] = index + 1 < n - 1 && signs[index + 1] === -signs[index] ? right[index + 1] + 1 : 2;
  }
  for (let index = 1; index < n - 1; index += 1) {
    const bridge = Math.sign(nums[index + 1] - nums[index - 1]);
    if (bridge === 0) continue;
    let before = left[index - 1];
    let after = right[index + 1];
    if (before > 1 && signs[index - 2] === bridge) before = 1;
    if (after > 1 && signs[index + 1] === bridge) after = 1;
    answer = Math.max(answer, before + after);
  }
  return answer;
}

const longestAlternating = solve;
class Solution {
  longestAlternating(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestAlternating };
