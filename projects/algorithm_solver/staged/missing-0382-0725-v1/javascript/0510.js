'use strict';

// 510. Inorder Successor in BST II. Use original parent links and return an existing node, not a copy.

function solve(node) {
  if (node.right) {
    node = node.right;
    while (node.left) node = node.left;
    return node;
  }
  while (node.parent && node.parent.right === node) node = node.parent;
  return node.parent || null;
}

const inorderSuccessor = solve;
class Solution {
  inorderSuccessor(node) { return solve(node); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, inorderSuccessor };
