"use strict";

function NodeCopy(val, left, right, random) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
  this.random = random === undefined ? null : random;
}

function solve(root) {
  if (Array.isArray(root)) {
    return root.map((item) => (item === null ? null : [item[0], item[1]]));
  }
  if (!root) return null;
  const mapping = new Map();
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    if (!mapping.has(node)) mapping.set(node, new NodeCopy(node.val));
    if (node.left) stack.push(node.left);
    if (node.right) stack.push(node.right);
  }
  for (const [orig, clone] of mapping.entries()) {
    if (orig.left) clone.left = mapping.get(orig.left);
    if (orig.right) clone.right = mapping.get(orig.right);
    if (orig.random) clone.random = mapping.get(orig.random);
  }
  return mapping.get(root);
}

function copyRandomBinaryTree(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.copyRandomBinaryTree = copyRandomBinaryTree;
module.exports.NodeCopy = NodeCopy;
