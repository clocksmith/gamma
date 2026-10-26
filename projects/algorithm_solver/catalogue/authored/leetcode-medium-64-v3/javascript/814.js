'use strict';

// 814. Binary Tree Pruning: prune zero-only child links in iterative postorder.
// O(n) time and O(n) auxiliary space; only zero-only child links are removed.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  if (root === null) return null;
  const kept = new Map();
  const stack = [[root, false]];
  while (stack.length) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]);
      if (node.right !== null) stack.push([node.right, false]);
      if (node.left !== null) stack.push([node.left, false]);
      continue;
    }
    if (!kept.get(node.left)) node.left = null;
    if (!kept.get(node.right)) node.right = null;
    kept.set(node, node.val !== 0 || node.left !== null || node.right !== null);
  }
  return kept.get(root) ? root : null;
}

const pruneTree = solve;
class Solution {
  pruneTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pruneTree, TreeNode };
