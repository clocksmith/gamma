"use strict";

function Node(val, children) {
  this.val = val === undefined ? null : val;
  this.children = children === undefined ? [] : children;
}

function fromNaryList(arr) {
  if (!arr || arr.length === 0 || arr[0] === null) return null;
  const root = new Node(arr[0], []);
  const q = [root];
  let head = 0, i = 2;
  while (head < q.length && i < arr.length) {
    const parent = q[head++];
    while (i < arr.length && arr[i] !== null && arr[i] !== undefined) {
      const child = new Node(arr[i], []);
      parent.children.push(child);
      q.push(child);
      i++;
    }
    i++;
  }
  return root;
}

function solve(root) {
  if (Array.isArray(root)) root = fromNaryList(root);
  if (!root) return 0;
  let depth = 0;
  const q = [root];
  let head = 0;
  while (head < q.length) {
    depth += 1;
    const end = q.length;
    while (head < end) {
      const node = q[head++];
      const ch = node.children || [];
      for (let i = 0; i < ch.length; i++) q.push(ch[i]);
    }
  }
  return depth;
}

function maxDepth(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxDepth = maxDepth;
module.exports.Node = Node;
