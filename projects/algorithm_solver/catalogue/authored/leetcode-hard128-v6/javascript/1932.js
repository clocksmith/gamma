'use strict';

// 1932. Merge BSTs to Create Single BST.
// Graft matching root values during iterative bounded BST traversal; O(n) time and space. Return fresh nodes and preserve all input trees.

class _TreeNode {
  constructor(val) { this.val = val; this.left = null; this.right = null; }
}
function solve(trees) {
  const roots = new Map(trees.map(tree => [tree.val, tree]));
  const leaves = new Set();
  for (const tree of trees) {
    if (tree.left != null) leaves.add(tree.left.val);
    if (tree.right != null) leaves.add(tree.right.val);
  }
  const candidates = [...roots.keys()].filter(value => !leaves.has(value));
  if (candidates.length !== 1) return null;
  const original = roots.get(candidates[0]);
  roots.delete(candidates[0]);
  const result = new _TreeNode(original.val);
  const stack = [[original, result, -Infinity, Infinity]];
  while (stack.length > 0) {
    let [source, target, lower, upper] = stack.pop();
    if (!(lower < source.val && source.val < upper)) return null;
    if (source.left == null && source.right == null && roots.has(source.val)) {
      const replacement = roots.get(source.val);
      roots.delete(source.val); source = replacement;
    }
    if (source.right != null) {
      target.right = new _TreeNode(source.right.val);
      stack.push([source.right, target.right, source.val, upper]);
    }
    if (source.left != null) {
      target.left = new _TreeNode(source.left.val);
      stack.push([source.left, target.left, lower, source.val]);
    }
  }
  return roots.size === 0 ? result : null;
}

const canMerge = solve;
class Solution {
  canMerge(trees) { return solve(trees); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canMerge };
