'use strict';

// 623. Add One Row to Tree. Insert the requested row in place while retaining all original descendant nodes.

class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root, val, depth) {
  if (depth === 1) return new TreeNode(val, root, null);
  let level = root ? [root] : [];
  for (let d = 1; d < depth - 1; d += 1) {
    const next = [];
    for (const node of level) { if (node.left) next.push(node.left); if (node.right) next.push(node.right); }
    level = next;
  }
  for (const node of level) {
    node.left = new TreeNode(val, node.left, null);
    node.right = new TreeNode(val, null, node.right);
  }
  return root;
}

const addOneRow = solve;
class Solution {
  addOneRow(root, val, depth) { return solve(root, val, depth); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addOneRow };
