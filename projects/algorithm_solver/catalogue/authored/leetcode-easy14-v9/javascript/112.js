'use strict';

// 112. Path Sum (Easy).
// Specification: https://leetcode.com/problems/path-sum/description/
// O(n) time, O(h) auxiliary space; accept only root-to-leaf paths and preserve the tree.
function solve(root, targetSum) {
  if (root === null) return false;
  const stack = [[root, targetSum - root.val]];
  while (stack.length > 0) {
    const [node, remaining] = stack.pop();
    if (node.left === null && node.right === null && remaining === 0) return true;
    if (node.right !== null) stack.push([node.right, remaining - node.right.val]);
    if (node.left !== null) stack.push([node.left, remaining - node.left.val]);
  }
  return false;
}

const hasPathSum = solve;
class Solution {
  hasPathSum(root, targetSum) { return solve(root, targetSum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasPathSum };
