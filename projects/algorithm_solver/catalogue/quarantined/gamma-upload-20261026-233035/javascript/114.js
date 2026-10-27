'use strict';
// 114. Flatten Binary Tree to Linked List.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root) {
  let current = root;
  while (current !== null) {
    if (current.left !== null) {
      let predecessor = current.left;
      while (predecessor.right !== null) predecessor = predecessor.right;
      predecessor.right = current.right;
      current.right = current.left;
      current.left = null;
    }
    current = current.right;
  }
}
const flatten = solve;
class Solution { flatten(root) { solve(root); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, flatten, TreeNode };
