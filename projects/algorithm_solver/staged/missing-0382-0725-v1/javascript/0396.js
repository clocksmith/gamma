'use strict';

// 396. Rotate Function. Update weighted sums between rotations; O(n) time.

function solve(nums) {
  let total = 0, current = 0;
  for (let i = 0; i < nums.length; i += 1) { total += nums[i]; current += i * nums[i]; }
  let answer = current;
  for (let i = nums.length - 1; i > 0; i -= 1) {
    current += total - nums.length * nums[i];
    answer = Math.max(answer, current);
  }
  return answer;
}

const maxRotateFunction = solve;
class Solution {
  maxRotateFunction(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxRotateFunction };
