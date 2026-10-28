'use strict';

// 2454. Next Greater Element IV (Hard).
// Specification: https://leetcode.com/problems/next-greater-element-iv/description/
function solve(nums) {
  const n = nums.length; const ans = new Array(n).fill(-1);
  for (let i = 0; i < n; i++) {
    let seen = 0;
    for (let j = i + 1; j < n; j++) {
      if (nums[j] > nums[i]) {
        seen++;
        if (seen === 2) { ans[i] = nums[j]; break; }
      }
    }
  }
  return ans;
}
const secondGreaterElement = solve;
class Solution { secondGreaterElement(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, secondGreaterElement };
