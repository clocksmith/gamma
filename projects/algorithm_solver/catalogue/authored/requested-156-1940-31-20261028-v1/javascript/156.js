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

function toLevel(root) {
  if (root === null || root === undefined) return [];
  const out = [];
  const q = [root];
  for (let i = 0; i < q.length; i++) {
    const node = q[i];
    if (node === null || node === undefined) {
      out.push(null);
    } else {
      out.push(node.val);
      q.push(node.left);
      q.push(node.right);
    }
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}

function solve(root) {
  const isArr = Array.isArray(root);
  let cur = toTree(root);
  let prev = null;
  let prevRight = null;
  while (cur !== null && cur !== undefined) {
    const nxt = cur.left;
    cur.left = prevRight;
    prevRight = cur.right;
    cur.right = prev;
    prev = cur;
    cur = nxt;
  }
  return isArr ? toLevel(prev) : prev;
}

function upsideDownBinaryTree(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.upsideDownBinaryTree = upsideDownBinaryTree;
module.exports.TreeNode = TreeNode;
