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
  if (!root) return [];
  const out = [];
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    if (node.left && !node.right) out.push(node.left.val);
    else if (node.right && !node.left) out.push(node.right.val);
    if (node.right) stack.push(node.right);
    if (node.left) stack.push(node.left);
  }
  return out;
}

function getLonelyNodes(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.getLonelyNodes = getLonelyNodes;
module.exports.TreeNode = TreeNode;
