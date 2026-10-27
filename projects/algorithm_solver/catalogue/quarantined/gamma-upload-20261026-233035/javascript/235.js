'use strict';
// 235. Lowest Common Ancestor of a Binary Search Tree.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root, p, q) {
  const low = Math.min(p.val, q.val); const high = Math.max(p.val, q.val);
  let current = root;
  while (current !== null) {
    if (current.val < low) current = current.right;
    else if (current.val > high) current = current.left;
    else return current;
  }
  return null;
}
const lowestCommonAncestor = solve;
class Solution { lowestCommonAncestor(root, p, q) { return solve(root, p, q); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lowestCommonAncestor, TreeNode };
