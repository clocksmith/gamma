'use strict';

// 496. Next Greater Element I.

function solve(nums1, nums2) {
  const stack = [], following = new Map();
  for (const value of nums2) {
    while (stack.length > 0 && stack[stack.length - 1] < value) following.set(stack.pop(), value);
    stack.push(value);
  }
  return nums1.map(value => following.has(value) ? following.get(value) : -1);
}

const nextGreaterElement = solve;
class Solution {
  nextGreaterElement(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextGreaterElement };
