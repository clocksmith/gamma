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
  if (head === null || head === undefined) return 0;
  let best = 0;
  function dfs(node, parentVal, curLen) {
    if (node === null || node === undefined) return;
    const ln = parentVal !== null && node.val === parentVal + 1 ? curLen + 1 : 1;
    if (ln > best) best = ln;
    dfs(node.left, node.val, ln);
    dfs(node.right, node.val, ln);
  }
  dfs(head, null, 0);
  return best;
}

function longestConsecutive(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.longestConsecutive = longestConsecutive;
module.exports.TreeNode = TreeNode;
