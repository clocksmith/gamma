'use strict';

// 654. Maximum Binary Tree. Monotone stack builds the Cartesian tree in O(n) time.

class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(nums) {
  const stack = [];
  for (const value of nums) {
    const node = new TreeNode(value);
    while (stack.length > 0 && stack[stack.length - 1].val < value) node.left = stack.pop();
    if (stack.length > 0) stack[stack.length - 1].right = node;
    stack.push(node);
  }
  return stack.length > 0 ? stack[0] : null;
}

const constructMaximumBinaryTree = solve;
class Solution {
  constructMaximumBinaryTree(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, constructMaximumBinaryTree };
