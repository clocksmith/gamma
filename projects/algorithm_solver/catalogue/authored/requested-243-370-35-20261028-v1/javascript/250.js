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
  let cnt = 0;
  function dfs(node) {
    if (node === null || node === undefined) return true;
    const okL = dfs(node.left);
    const okR = dfs(node.right);
    if (!okL || !okR) return false;
    if (node.left !== null && node.left.val !== node.val) return false;
    if (node.right !== null && node.right.val !== node.val) return false;
    cnt++;
    return true;
  }
  dfs(head);
  return cnt;
}

function countUnivalSubtrees(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countUnivalSubtrees = countUnivalSubtrees;
module.exports.TreeNode = TreeNode;
