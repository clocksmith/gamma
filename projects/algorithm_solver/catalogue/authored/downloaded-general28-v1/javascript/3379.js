'use strict';

// 3379. Transformed Array (Easy).
// Specification: https://leetcode.com/problems/transformed-array/description/
function solve(nums) {
  const n = nums.length;
  const res = [];
  for (let i = 0; i < n; i++) {
    if (nums[i] === 0) res.push(0);
    else res.push(nums[((i + nums[i]) % n + n) % n]);
  }
  return res;
}
const constructTransformedArray = solve;
class Solution { constructTransformedArray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, constructTransformedArray };
