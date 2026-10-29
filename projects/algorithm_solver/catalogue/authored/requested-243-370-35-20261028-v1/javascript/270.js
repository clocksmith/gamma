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

function solve(root, target) {
  let cur = toTree(root);
  let best = cur.val;
  while (cur !== null && cur !== undefined) {
    const v = cur.val;
    const d1 = Math.abs(v - target);
    const d2 = Math.abs(best - target);
    if (d1 < d2 || (d1 === d2 && v < best)) best = v;
    cur = target < v ? cur.left : cur.right;
  }
  return best;
}

function closestValue(root, target) {
  return solve(root, target);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.closestValue = closestValue;
module.exports.TreeNode = TreeNode;
