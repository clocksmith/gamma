'use strict';

// 814. Binary Tree Pruning: build a pruned copy in iterative postorder.
// O(n) time and O(n) auxiliary space excluding the returned tree; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  if (root === null) return null;
  const copies = new Map();
  const stack = [[root, false]];
  while (stack.length) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]);
      if (node.right !== null) stack.push([node.right, false]);
      if (node.left !== null) stack.push([node.left, false]);
      continue;
    }
    const left = copies.get(node.left) || null;
    const right = copies.get(node.right) || null;
    copies.set(node, node.val !== 0 || left !== null || right !== null ? new TreeNode(node.val, left, right) : null);
  }
  return copies.get(root);
}

const pruneTree = solve;
class Solution {
  pruneTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pruneTree, TreeNode };
