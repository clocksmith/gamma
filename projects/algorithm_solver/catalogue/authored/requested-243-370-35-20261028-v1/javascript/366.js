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

function solve(root) {
  const head = toTree(root);
  const res = [];
  function dfs(node) {
    if (node === null || node === undefined) return -1;
    const hl = dfs(node.left);
    const hr = dfs(node.right);
    const h = 1 + (hl > hr ? hl : hr);
    if (h === res.length) res.push([]);
    res[h].push(node.val);
    return h;
  }
  dfs(head);
  return res;
}

function findLeaves(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findLeaves = findLeaves;
module.exports.TreeNode = TreeNode;
