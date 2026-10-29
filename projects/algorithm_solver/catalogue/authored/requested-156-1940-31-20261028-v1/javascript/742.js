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

function solve(root, k) {
  const head = toTree(root);
  const adj = new Map();
  const leaves = new Set();
  function addEdge(u, v) {
    if (!adj.has(u)) adj.set(u, []);
    adj.get(u).push(v);
  }
  function dfs(node, par) {
    if (node === null || node === undefined) return;
    const u = node.val;
    if (par !== null) {
      addEdge(u, par);
      addEdge(par, u);
    }
    if (node.left === null && node.right === null) leaves.add(u);
    dfs(node.left, u);
    dfs(node.right, u);
  }
  dfs(head, null);
  const q = [k];
  const vis = new Set([k]);
  for (let i = 0; i < q.length; i++) {
    const u = q[i];
    if (leaves.has(u)) return u;
    const nb = adj.get(u) || [];
    for (let j = 0; j < nb.length; j++) {
      const v = nb[j];
      if (!vis.has(v)) {
        vis.add(v);
        q.push(v);
      }
    }
  }
  return k;
}

function findClosestLeaf(root, k) {
  return solve(root, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findClosestLeaf = findClosestLeaf;
module.exports.TreeNode = TreeNode;
