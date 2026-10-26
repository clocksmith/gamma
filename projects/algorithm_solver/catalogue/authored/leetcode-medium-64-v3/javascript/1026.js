'use strict';

// 1026. Maximum Difference Between Node and Ancestor: carry the path minimum and maximum through an explicit stack.
// O(n) time and O(h) auxiliary space for height h; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  if (root === null) return 0;
  let best = 0;
  const stack = [[root, root.val, root.val]];
  while (stack.length) {
    const [node, pathLow, pathHigh] = stack.pop();
    const low = Math.min(pathLow, node.val);
    const high = Math.max(pathHigh, node.val);
    best = Math.max(best, high - low);
    if (node.left !== null) stack.push([node.left, low, high]);
    if (node.right !== null) stack.push([node.right, low, high]);
  }
  return best;
}

const maxAncestorDiff = solve;
class Solution {
  maxAncestorDiff(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAncestorDiff, TreeNode };
