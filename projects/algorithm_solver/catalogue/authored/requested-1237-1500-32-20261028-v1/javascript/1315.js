"use strict";

function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function fromLevel(arr) {
  if (!arr || arr.length === 0 || arr[0] === null) return null;
  const root = new TreeNode(arr[0]);
  const q = [root];
  let head = 0, i = 1;
  while (head < q.length && i < arr.length) {
    const n = q[head++];
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) { n.left = new TreeNode(v); q.push(n.left); }
    }
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) { n.right = new TreeNode(v); q.push(n.right); }
    }
  }
  return root;
}

function solve(root) {
  if (Array.isArray(root)) root = fromLevel(root);
  if (!root) return 0;
  let total = 0;
  const stack = [[root, 1, 1]];
  while (stack.length > 0) {
    const [node, p, gp] = stack.pop();
    if ((gp & 1) === 0) total += node.val;
    if (node.left) stack.push([node.left, node.val, p]);
    if (node.right) stack.push([node.right, node.val, p]);
  }
  return total;
}

function sumEvenGrandparent(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.sumEvenGrandparent = sumEvenGrandparent;
module.exports.TreeNode = TreeNode;
