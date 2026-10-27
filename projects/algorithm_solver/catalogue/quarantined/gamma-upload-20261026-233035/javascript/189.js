'use strict';
// 189. Rotate Array.
function reverseRange(nums, left, right) {
  while (left < right) { [nums[left], nums[right]] = [nums[right], nums[left]]; left += 1; right -= 1; }
}
function solve(nums, k) {
  if (nums.length === 0) return;
  k %= nums.length;
  reverseRange(nums, 0, nums.length - 1);
  reverseRange(nums, 0, k - 1);
  reverseRange(nums, k, nums.length - 1);
}
const rotate = solve;
class Solution { rotate(nums, k) { solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotate };
