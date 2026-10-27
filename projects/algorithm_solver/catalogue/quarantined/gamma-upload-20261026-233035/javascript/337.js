'use strict';
// 337. House Robber III.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root) {
  function visit(node) {
    if (node === null) return [0, 0];
    const [leftSkip, leftTake] = visit(node.left);
    const [rightSkip, rightTake] = visit(node.right);
    return [Math.max(leftSkip, leftTake) + Math.max(rightSkip, rightTake), node.val + leftSkip + rightSkip];
  }
  return Math.max(...visit(root));
}
const rob = solve;
class Solution { rob(root) { return solve(root); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rob, TreeNode };
