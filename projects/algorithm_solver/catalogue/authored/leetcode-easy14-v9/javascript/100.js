'use strict';

// 100. Same Tree (Easy).
// Specification: https://leetcode.com/problems/same-tree/description/
// O(n) time, O(h) auxiliary space; compare shape and values without modifying either tree.
function solve(p, q) {
  const stack = [[p, q]];
  while (stack.length > 0) {
    const [first, second] = stack.pop();
    if (first === null || second === null) {
      if (first !== second) return false;
      continue;
    }
    if (first.val !== second.val) return false;
    stack.push([first.right, second.right]);
    stack.push([first.left, second.left]);
  }
  return true;
}

const isSameTree = solve;
class Solution {
  isSameTree(p, q) { return solve(p, q); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isSameTree };
