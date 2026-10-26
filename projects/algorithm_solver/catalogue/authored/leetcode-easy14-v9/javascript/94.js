'use strict';

// 94. Binary Tree Inorder Traversal (Easy).
// Specification: https://leetcode.com/problems/binary-tree-inorder-traversal/description/
// O(n) time, O(h) auxiliary space excluding the result; preserve every node and link.
function solve(root) {
  const result = [];
  const stack = [];
  let current = root;
  while (current !== null || stack.length > 0) {
    while (current !== null) {
      stack.push(current);
      current = current.left;
    }
    current = stack.pop();
    result.push(current.val);
    current = current.right;
  }
  return result;
}

const inorderTraversal = solve;
class Solution {
  inorderTraversal(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, inorderTraversal };
