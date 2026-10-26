'use strict';

// 3738. Longest Non-Decreasing Subarray After Replacing at Most One Element.
// O(n) time and O(n) space; bridge adjacent monotone runs only when one replacement can join them.
function solve(nums) {
  const n = nums.length;
  const left = new Int32Array(n).fill(1);
  const right = new Int32Array(n).fill(1);
  let answer = 1;
  for (let index = 1; index < n; index += 1) {
    if (nums[index - 1] <= nums[index]) left[index] = left[index - 1] + 1;
    answer = Math.max(answer, left[index]);
  }
  for (let index = n - 2; index >= 0; index -= 1) {
    if (nums[index] <= nums[index + 1]) right[index] = right[index + 1] + 1;
  }
  for (let index = 0; index < n; index += 1) {
    const before = index > 0 ? left[index - 1] : 0;
    const after = index + 1 < n ? right[index + 1] : 0;
    answer = Math.max(answer, before + 1, after + 1);
    if (index > 0 && index + 1 < n && nums[index - 1] <= nums[index + 1]) answer = Math.max(answer, before + after + 1);
  }
  return answer;
}

const longestSubarray = solve;
class Solution {
  longestSubarray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubarray };
