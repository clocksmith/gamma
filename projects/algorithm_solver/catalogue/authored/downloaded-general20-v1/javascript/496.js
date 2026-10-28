'use strict';

// 496. Next Greater Element I (Easy).
// Specification: https://leetcode.com/problems/next-greater-element-i/description/
function solve(nums1, nums2) {
  const nextGreater = new Map();
  const stack = [];
  for (const value of nums2) {
    while (stack.length > 0 && stack[stack.length - 1] < value) nextGreater.set(stack.pop(), value);
    stack.push(value);
  }
  while (stack.length > 0) nextGreater.set(stack.pop(), -1);
  return nums1.map((value) => nextGreater.get(value));
}

const nextGreaterElement = solve;
class Solution {
  nextGreaterElement(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextGreaterElement };
