'use strict';

// 783. Minimum Distance Between BST Nodes (Easy).
// Specification: https://leetcode.com/problems/minimum-distance-between-bst-nodes/description/
// O(n) time, O(h) auxiliary space; preserve the supplied tree.
function solve(root) {
  const stack = [];
  let node = root;
  let previous = null;
  let smallest = Infinity;
  while (node !== null || stack.length > 0) {
    while (node !== null) {
      stack.push(node);
      node = node.left;
    }
    node = stack.pop();
    if (previous !== null) smallest = Math.min(smallest, node.val - previous);
    previous = node.val;
    node = node.right;
  }
  return smallest;
}

const minDiffInBST = solve;
class Solution {
  minDiffInBST(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDiffInBST };
