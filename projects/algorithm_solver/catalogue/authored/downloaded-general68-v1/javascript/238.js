'use strict';

// 238. Product of Array Except Self (Medium).
// Specification: https://leetcode.com/problems/product-of-array-except-self/description/
function solve(nums) {
  const answer = new Array(nums.length).fill(1);
  let prefix = 1;
  for (let i = 0; i < nums.length; i++) { answer[i] = prefix; prefix *= nums[i]; }
  let suffix = 1;
  for (let i = nums.length - 1; i >= 0; i--) { answer[i] *= suffix; suffix *= nums[i]; }
  return answer;
}
const productExceptSelf = solve;
class Solution { productExceptSelf(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, productExceptSelf };
