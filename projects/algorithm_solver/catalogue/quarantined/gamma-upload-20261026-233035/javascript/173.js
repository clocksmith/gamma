'use strict';
// 173. Binary Search Tree Iterator.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
class BSTIterator {
  constructor(root) { this.stack = []; this.pushLeft(root); }
  pushLeft(node) { while (node !== null) { this.stack.push(node); node = node.left; } }
  next() { const node = this.stack.pop(); this.pushLeft(node.right); return node.val; }
  hasNext() { return this.stack.length > 0; }
}
function solve(root, operations) {
  const iterator = new BSTIterator(root);
  return operations.map(operation => iterator[operation]());
}
if (typeof module !== 'undefined') module.exports = { solve, BSTIterator, TreeNode };
