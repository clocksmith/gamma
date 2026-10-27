'use strict';

// 700. Search in a Binary Search Tree. Return the original matching subtree without copying or mutation.

function solve(root, val) {
  while (root && root.val !== val) root = val < root.val ? root.left : root.right;
  return root;
}

const searchBST = solve;
class Solution {
  searchBST(root, val) { return solve(root, val); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, searchBST };
