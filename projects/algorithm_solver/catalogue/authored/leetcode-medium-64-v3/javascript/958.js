'use strict';

// 958. Check Completeness of a Binary Tree: reject a nonempty level-order position after the first gap.
// O(n) time and O(n) auxiliary space; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  const queue = [root];
  let head = 0;
  let gap = false;
  while (head < queue.length) {
    const node = queue[head];
    head += 1;
    if (node === null) gap = true;
    else {
      if (gap) return false;
      queue.push(node.left, node.right);
    }
  }
  return true;
}

const isCompleteTree = solve;
class Solution {
  isCompleteTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isCompleteTree, TreeNode };
