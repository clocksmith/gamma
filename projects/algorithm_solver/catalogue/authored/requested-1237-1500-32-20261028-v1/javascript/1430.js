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

function solve(root, arr) {
  if (Array.isArray(root)) root = fromLevel(root);
  const stack = [[root, 0]];
  const m = arr.length;
  while (stack.length > 0) {
    const [node, idx] = stack.pop();
    if (!node || idx >= m || node.val !== arr[idx]) continue;
    if (!node.left && !node.right) {
      if (idx === m - 1) return true;
    } else {
      stack.push([node.left, idx + 1], [node.right, idx + 1]);
    }
  }
  return false;
}

function isValidSequence(root, arr) {
  return solve(root, arr);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isValidSequence = isValidSequence;
module.exports.TreeNode = TreeNode;
