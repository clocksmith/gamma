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

class FindElements {
  constructor(root) {
    if (Array.isArray(root)) root = fromLevel(root);
    const seen = new Set();
    if (root) {
      const stack = [[root, 0]];
      while (stack.length > 0) {
        const [node, v] = stack.pop();
        seen.add(v);
        if (node.left) stack.push([node.left, 2 * v + 1]);
        if (node.right) stack.push([node.right, 2 * v + 2]);
      }
    }
    this.seen = seen;
  }
  find(target) {
    return this.seen.has(target);
  }
}

function solve(operation_names, argument_lists) {
  const inst = new FindElements(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    out.push(inst.find(argument_lists[i][0]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.FindElements = FindElements;
module.exports.TreeNode = TreeNode;
