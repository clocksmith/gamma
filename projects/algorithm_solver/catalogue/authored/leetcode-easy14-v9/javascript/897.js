'use strict';

// 897. Increasing Order Search Tree (Easy).
// Specification: https://leetcode.com/problems/increasing-order-search-tree/description/
// O(n) time, O(h) space; rewire the original nodes into an increasing right-only chain.
function solve(root) {
  const stack = [];
  let current = root;
  let head = null;
  let tail = null;
  while (current !== null || stack.length > 0) {
    while (current !== null) {
      stack.push(current);
      current = current.left;
    }
    current = stack.pop();
    const nextRoot = current.right;
    current.left = null;
    if (tail === null) {
      head = current;
    } else {
      tail.right = current;
    }
    tail = current;
    current = nextRoot;
  }
  if (tail !== null) tail.right = null;
  return head;
}

const increasingBST = solve;
class Solution {
  increasingBST(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, increasingBST };
