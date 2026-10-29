"use strict";

function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function toTree(root) {
  if (!Array.isArray(root)) return root;
  if (root.length === 0 || root[0] === null) return null;
  const nodes = root.map((v) => (v === null ? null : new TreeNode(v)));
  let idx = 1;
  for (let i = 0; i < nodes.length && idx < nodes.length; i++) {
    if (nodes[i] !== null) {
      if (idx < nodes.length) nodes[i].left = nodes[idx++];
      if (idx < nodes.length) nodes[i].right = nodes[idx++];
    }
  }
  return nodes[0];
}

function solve(root, target, k) {
  const head = toTree(root);
  const vals = [];
  function inorder(node) {
    if (node === null || node === undefined) return;
    inorder(node.left);
    vals.push(node.val);
    inorder(node.right);
  }
  inorder(head);
  let lo = 0;
  for (let i = k; i < vals.length; i++) {
    if (Math.abs(vals[i] - target) < Math.abs(vals[lo] - target)) lo++;
    else break;
  }
  return vals.slice(lo, lo + k);
}

function closestKValues(root, target, k) {
  return solve(root, target, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.closestKValues = closestKValues;
module.exports.TreeNode = TreeNode;
