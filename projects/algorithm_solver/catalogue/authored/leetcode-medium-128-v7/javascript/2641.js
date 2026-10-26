'use strict';

// 2641. Cousins in Binary Tree II: build a new tree from level totals minus each sibling group.
// O(n) time and O(n) auxiliary space including the independent result tree; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  if (root === null) return null;
  const result = new TreeNode(0);
  let level = [[root, result]];
  while (level.length) {
    let total = 0;
    for (const [original] of level) {
      if (original.left !== null) total += original.left.val;
      if (original.right !== null) total += original.right.val;
    }
    const following = [];
    for (const [original, copied] of level) {
      const siblings = (original.left === null ? 0 : original.left.val)
        + (original.right === null ? 0 : original.right.val);
      if (original.left !== null) {
        copied.left = new TreeNode(total - siblings);
        following.push([original.left, copied.left]);
      }
      if (original.right !== null) {
        copied.right = new TreeNode(total - siblings);
        following.push([original.right, copied.right]);
      }
    }
    level = following;
  }
  return result;
}

const replaceValueInTree = solve;
class Solution {
  replaceValueInTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, replaceValueInTree, TreeNode };
