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
  const sizes = [];
  function dfs(node) {
    if (node === null || node === undefined) return [true, 0];
    const [okL, hl] = dfs(node.left);
    const [okR, hr] = dfs(node.right);
    if (okL && okR && hl === hr) {
      const h = hl + 1;
      sizes.push((1 << h) - 1);
      return [true, h];
    }
    return [false, 0];
  }
  dfs(head);
  sizes.sort((a, b) => b - a);
  return sizes.length >= k ? sizes[k - 1] : -1;
}

function kthLargestPerfectSubtree(root, k) {
  return solve(root, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.kthLargestPerfectSubtree = kthLargestPerfectSubtree;
module.exports.TreeNode = TreeNode;
