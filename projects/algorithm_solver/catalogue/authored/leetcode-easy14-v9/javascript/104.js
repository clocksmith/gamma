'use strict';

// 104. Maximum Depth of Binary Tree (Easy).
// Specification: https://leetcode.com/problems/maximum-depth-of-binary-tree/description/
// O(n) time, O(h) auxiliary space; use an explicit traversal stack and preserve the tree.
function solve(root) {
  if (root === null) return 0;
  const stack = [[root, 1]];
  let deepest = 0;
  while (stack.length > 0) {
    const [node, depth] = stack.pop();
    deepest = Math.max(deepest, depth);
    if (node.right !== null) stack.push([node.right, depth + 1]);
    if (node.left !== null) stack.push([node.left, depth + 1]);
  }
  return deepest;
}

const maxDepth = solve;
class Solution {
  maxDepth(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDepth };
