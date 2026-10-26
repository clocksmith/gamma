'use strict';

// 1382. Balance a Binary Search Tree: rebuild fresh nodes from an iterative inorder sequence.
// O(n) time and O(n) auxiliary space; reconstruction depth is O(log n); inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  const ordered = [];
  const stack = [];
  let current = root;
  while (current !== null || stack.length) {
    while (current !== null) {
      stack.push(current);
      current = current.left;
    }
    current = stack.pop();
    ordered.push(current.val);
    current = current.right;
  }
  function build(left, right) {
    if (left >= right) return null;
    const middle = Math.floor((left + right) / 2);
    return new TreeNode(ordered[middle], build(left, middle), build(middle + 1, right));
  }
  return build(0, ordered.length);
}

const balanceBST = solve;
class Solution {
  balanceBST(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, balanceBST, TreeNode };
