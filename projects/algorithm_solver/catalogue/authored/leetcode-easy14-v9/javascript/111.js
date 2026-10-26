'use strict';

// 111. Minimum Depth of Binary Tree (Easy).
// Specification: https://leetcode.com/problems/minimum-depth-of-binary-tree/description/
// O(n) time, O(w) space; visit complete levels until the first leaf and preserve the tree.
function solve(root) {
  if (root === null) return 0;
  let level = [root];
  let depth = 1;
  while (level.length > 0) {
    const nextLevel = [];
    for (const node of level) {
      if (node.left === null && node.right === null) return depth;
      if (node.left !== null) nextLevel.push(node.left);
      if (node.right !== null) nextLevel.push(node.right);
    }
    level = nextLevel;
    depth++;
  }
  return 0;
}

const minDepth = solve;
class Solution {
  minDepth(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDepth };
