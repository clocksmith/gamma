'use strict';
// 236. Lowest Common Ancestor of a Binary Tree.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root, p, q) {
  if (root === null || root === p || root === q) return root;
  const left = solve(root.left, p, q);
  const right = solve(root.right, p, q);
  return left !== null && right !== null ? root : left || right;
}
const lowestCommonAncestor = solve;
class Solution { lowestCommonAncestor(root, p, q) { return solve(root, p, q); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lowestCommonAncestor, TreeNode };
