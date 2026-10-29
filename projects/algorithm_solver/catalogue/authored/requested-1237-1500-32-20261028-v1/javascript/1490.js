"use strict";

function Node(val, children) {
  this.val = val === undefined ? null : val;
  this.children = children === undefined ? [] : children;
}

function solve(root) {
  if (Array.isArray(root)) return root.slice();
  if (!root) return null;
  const clone = new Node(root.val, []);
  const stack = [[root, clone]];
  while (stack.length > 0) {
    const [orig, copy] = stack.pop();
    const ch = orig.children || [];
    for (let i = 0; i < ch.length; i++) {
      const chCopy = new Node(ch[i].val, []);
      copy.children.push(chCopy);
      stack.push([ch[i], chCopy]);
    }
  }
  return clone;
}

function cloneTree(root) {
  return solve(root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.cloneTree = cloneTree;
module.exports.Node = Node;
