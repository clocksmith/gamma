'use strict';
// 285. Inorder Successor in BST.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root, p) {
  let successor = null; let current = root;
  while (current !== null) {
    if (p.val < current.val) { successor = current; current = current.left; }
    else current = current.right;
  }
  return successor;
}
const inorderSuccessor = solve;
class Solution { inorderSuccessor(root, p) { return solve(root, p); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, inorderSuccessor, TreeNode };
