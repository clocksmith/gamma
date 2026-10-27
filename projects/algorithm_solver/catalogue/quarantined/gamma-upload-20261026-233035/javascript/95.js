'use strict';
// 95. Unique Binary Search Trees II.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function clone(root) {
  return root === null ? null : new TreeNode(root.val, clone(root.left), clone(root.right));
}
function solve(n) {
  function build(low, high) {
    if (low > high) return [null];
    const trees = [];
    for (let value = low; value <= high; value += 1) {
      for (const left of build(low, value - 1)) for (const right of build(value + 1, high)) {
        trees.push(new TreeNode(value, clone(left), clone(right)));
      }
    }
    return trees;
  }
  return n === 0 ? [] : build(1, n);
}
const generateTrees = solve;
class Solution { generateTrees(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, generateTrees, TreeNode };
