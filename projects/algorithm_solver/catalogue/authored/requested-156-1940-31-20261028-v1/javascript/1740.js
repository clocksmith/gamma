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

function solve(root, p, q) {
  if (p === q) return 0;
  const head = toTree(root);
  function lca(node) {
    if (node === null || node === undefined || node.val === p || node.val === q) return node;
    const l = lca(node.left);
    const r = lca(node.right);
    if (l !== null && r !== null) return node;
    return l !== null ? l : r;
  }
  function dist(node, target, d) {
    if (node === null || node === undefined) return -1;
    if (node.val === target) return d;
    const dl = dist(node.left, target, d + 1);
    return dl !== -1 ? dl : dist(node.right, target, d + 1);
  }
  const anc = lca(head);
  return dist(anc, p, 0) + dist(anc, q, 0);
}

function findDistance(root, p, q) {
  return solve(root, p, q);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findDistance = findDistance;
module.exports.TreeNode = TreeNode;
