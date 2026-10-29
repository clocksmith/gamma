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
  if (head === null || head === undefined) return [];
  const cols = new Map();
  const q = [[head, 0]];
  let minC = 0, maxC = 0;
  for (let i = 0; i < q.length; i++) {
    const [node, c] = q[i];
    if (!cols.has(c)) cols.set(c, []);
    cols.get(c).push(node.val);
    if (c < minC) minC = c;
    if (c > maxC) maxC = c;
    if (node.left !== null) q.push([node.left, c - 1]);
    if (node.right !== null) q.push([node.right, c + 1]);
  }
  const out = [];
  for (let c = minC; c <= maxC; c++) out.push(cols.get(c));
  return out;
}

function verticalOrder(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.verticalOrder = verticalOrder;
module.exports.TreeNode = TreeNode;
