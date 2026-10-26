'use strict';

// 2196. Create Binary Tree From Descriptions: create each node once and locate the parent without an incoming edge.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(descriptions) {
  const nodes = new Map();
  const children = new Set();
  for (const [parent, child, isLeft] of descriptions) {
    if (!nodes.has(parent)) nodes.set(parent, new TreeNode(parent));
    if (!nodes.has(child)) nodes.set(child, new TreeNode(child));
    if (isLeft) nodes.get(parent).left = nodes.get(child);
    else nodes.get(parent).right = nodes.get(child);
    children.add(child);
  }
  for (const [value, node] of nodes) {
    if (!children.has(value)) return node;
  }
  return null;
}

const createBinaryTree = solve;
class Solution {
  createBinaryTree(descriptions) { return solve(descriptions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, createBinaryTree, TreeNode };
