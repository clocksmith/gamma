'use strict';

// 189. Rotate Array (Medium).
// Specification: https://leetcode.com/problems/rotate-array/description/
function solve(nums, k) {
  const n = nums.length;
  if (n === 0) return [];
  const steps = ((k % n) + n) % n;
  return nums.slice(n - steps).concat(nums.slice(0, n - steps));
}
const rotate = (nums, k) => new Solution().rotate(nums, k);
class Solution { rotate(nums, k) {
  const size = nums.length, steps = k % size;
  if (steps === 0) return;
  function reverse(left, right) {
    while (left < right) {
      const value = nums[left]; nums[left] = nums[right]; nums[right] = value;
      left++; right--;
    }
  }
  reverse(0, size - 1); reverse(0, steps - 1); reverse(steps, size - 1);
} }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotate };
