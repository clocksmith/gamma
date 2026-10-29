"use strict";

function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function fromLevel(arr) {
  if (!arr || arr.length === 0 || arr[0] === null) return null;
  const root = new TreeNode(arr[0]);
  const q = [root];
  let head = 0, i = 1;
  while (head < q.length && i < arr.length) {
    const n = q[head++];
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) { n.left = new TreeNode(v); q.push(n.left); }
    }
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) { n.right = new TreeNode(v); q.push(n.right); }
    }
  }
  return root;
}

function solve(root) {
  if (Array.isArray(root)) root = fromLevel(root);
  if (!root) return 0;
  const q = [root];
  let head = 0, levelSum = 0;
  while (head < q.length) {
    const end = q.length;
    levelSum = 0;
    while (head < end) {
      const node = q[head++];
      levelSum += node.val;
      if (node.left) q.push(node.left);
      if (node.right) q.push(node.right);
    }
  }
  return levelSum;
}

function deepestLeavesSum(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.deepestLeavesSum = deepestLeavesSum;
module.exports.TreeNode = TreeNode;
