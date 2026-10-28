'use strict';

// 457. Circular Array Loop (Medium).
// Specification: https://leetcode.com/problems/circular-array-loop/description/
function nextIndex(nums, index) {
  const n = nums.length;
  return ((index + nums[index]) % n + n) % n;
}
function solve(nums) {
  const n = nums.length;
  for (let start = 0; start < n; start++) {
    let slow = start; let fast = start;
    const direction = nums[start] > 0;
    while (true) {
      slow = nextIndex(nums, slow);
      if ((nums[slow] > 0) !== direction) break;
      fast = nextIndex(nums, fast);
      if ((nums[fast] > 0) !== direction) break;
      fast = nextIndex(nums, fast);
      if ((nums[fast] > 0) !== direction) break;
      if (slow === fast) {
        if (slow === nextIndex(nums, slow)) break;
        return true;
      }
    }
  }
  return false;
}
const circularArrayLoop = solve;
class Solution { circularArrayLoop(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, circularArrayLoop };
