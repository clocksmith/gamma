'use strict';

// 1339. Maximum Product of Splitted Binary Tree: compare exact products of subtree sums before taking the modulus.
// O(n) time and O(n) auxiliary space on the bounded integer domain; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  if (root === null) return 0;
  const order = [root];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    if (node.left !== null) order.push(node.left);
    if (node.right !== null) order.push(node.right);
  }
  const sums = new Map();
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    sums.set(node, node.val + (sums.get(node.left) || 0) + (sums.get(node.right) || 0));
  }
  const total = sums.get(root);
  let best = 0n;
  for (let index = 1; index < order.length; index += 1) {
    const part = sums.get(order[index]);
    const product = BigInt(part) * BigInt(total - part);
    if (product > best) best = product;
  }
  return Number(best % 1000000007n);
}

const maxProduct = solve;
class Solution {
  maxProduct(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct, TreeNode };
