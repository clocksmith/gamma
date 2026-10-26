'use strict';

// 1372. Longest ZigZag Path in a Binary Tree: carry alternating path lengths without recursive traversal.
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
  const stack = [[root, 0, 0]];
  let best = 0;
  while (stack.length) {
    const [node, fromLeft, fromRight] = stack.pop();
    best = Math.max(best, fromLeft, fromRight);
    if (node.left !== null) stack.push([node.left, fromRight + 1, 0]);
    if (node.right !== null) stack.push([node.right, 0, fromLeft + 1]);
  }
  return best;
}

const longestZigZag = solve;
class Solution {
  longestZigZag(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestZigZag, TreeNode };
