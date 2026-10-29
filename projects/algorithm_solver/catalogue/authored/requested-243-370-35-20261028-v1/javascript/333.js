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
  function dfs(node) {
    if (node === null || node === undefined) return [true, Infinity, -Infinity, 0];
    const [okL, mnL, mxL, szL] = dfs(node.left);
    const [okR, mnR, mxR, szR] = dfs(node.right);
    if (okL && okR && mxL < node.val && node.val < mnR) {
      return [true, Math.min(mnL, node.val), Math.max(mxR, node.val), szL + szR + 1];
    }
    return [false, -Infinity, Infinity, Math.max(szL, szR)];
  }
  return dfs(head)[3];
}

function largestBSTSubtree(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.largestBSTSubtree = largestBSTSubtree;
module.exports.TreeNode = TreeNode;
