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

function solve(original, cloned, target) {
  if (target === undefined) {
    const root = fromLevel(original);
    const stack = [root];
    while (stack.length > 0) {
      const n = stack.pop();
      if (n) {
        if (n.val === cloned) return n.val;
        stack.push(n.left, n.right);
      }
    }
    return cloned;
  }
  const stack = [[original, cloned]];
  while (stack.length > 0) {
    const [o, c] = stack.pop();
    if (!o) continue;
    if (o === target || o.val === target.val) return c;
    stack.push([o.left, c.left], [o.right, c.right]);
  }
  return null;
}

function getTargetCopy(original, cloned, target) {
  return solve(original, cloned, target);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.getTargetCopy = getTargetCopy;
module.exports.TreeNode = TreeNode;
