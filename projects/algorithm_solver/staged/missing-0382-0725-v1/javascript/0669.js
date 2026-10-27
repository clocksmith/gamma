'use strict';

// 669. Trim a Binary Search Tree. Trim original links in place while preserving the surviving nodes and their relative structure.

function solve(root, low, high) {
  while (root && (root.val < low || root.val > high)) root = root.val < low ? root.right : root.left;
  if (root === null) return null;
  let node = root;
  while (node) {
    while (node.left && node.left.val < low) node.left = node.left.right;
    node = node.left;
  }
  node = root;
  while (node) {
    while (node.right && node.right.val > high) node.right = node.right.left;
    node = node.right;
  }
  return root;
}

const trimBST = solve;
class Solution {
  trimBST(root, low, high) { return solve(root, low, high); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, trimBST };
