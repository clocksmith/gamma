/**
 * 3997. Count Dominant Nodes in a Binary Tree
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-dominant-nodes-in-a-binary-tree/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3997.Count%20Dominant%20Nodes%20in%20a%20Binary%20Tree/README_EN.md
 * Complexity: O(n) time, O(log n) stack on the guaranteed complete binary tree.
 * Native TreeNode objects with val/left/right; input tree is preserved. Equal maxima count as dominant; no array transport is inferred.
 */

function solve(root) {
  function visit(node) {
    if (node == null) return [-Infinity, 0];
    const [left, lc] = visit(node.left), [right, rc] = visit(node.right);
    const maximum = Math.max(node.val, left, right);
    return [maximum, lc + rc + Number(node.val === maximum)];
  }
  return visit(root)[1];
}

function countDominantNodes(root) {
  return solve(root);
}

class Solution {
  countDominantNodes(root) {
    return solve(root);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countDominantNodes, Solution };
}
