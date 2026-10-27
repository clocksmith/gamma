'use strict';

// 701. Insert into a Binary Search Tree. Insert one new leaf and retain existing nodes.

class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root, val) {
  if (root === null) return new TreeNode(val);
  let node = root;
  while (true) {
    if (val < node.val) {
      if (node.left === null) { node.left = new TreeNode(val); break; }
      node = node.left;
    } else {
      if (node.right === null) { node.right = new TreeNode(val); break; }
      node = node.right;
    }
  }
  return root;
}

const insertIntoBST = solve;
class Solution {
  insertIntoBST(root, val) { return solve(root, val); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, insertIntoBST };
