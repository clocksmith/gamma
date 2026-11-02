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

// Deep-copies a caller's node graph so the pure entrypoint never rotates or
// aliases caller nodes. Iterative (no recursion depth limit); a node reached
// twice (cycle or shared child) is not a binary tree and is rejected. The
// copy keeps each node's prototype so a caller-supplied TreeNode class survives.
function cloneTree(root) {
  if (root === null || root === undefined) return null;
  const seen = new Map();
  const copyOf = (node) => {
    if (node === null || node === undefined) return null;
    if (seen.has(node)) throw new TypeError("upsideDownBinaryTree: input is not a tree (node reached twice)");
    const copy = Object.create(Object.getPrototypeOf(node));
    copy.val = node.val;
    copy.left = null;
    copy.right = null;
    seen.set(node, copy);
    return copy;
  };
  const head = copyOf(root);
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    const copy = seen.get(node);
    copy.left = copyOf(node.left);
    copy.right = copyOf(node.right);
    if (node.left !== null && node.left !== undefined) stack.push(node.left);
    if (node.right !== null && node.right !== undefined) stack.push(node.right);
  }
  return head;
}

// In-place left-spine pointer rotation on nodes the caller of rotate owns.
function rotate(root) {
  let cur = root;
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
  return prev;
}

// Pure value-domain entrypoint: inputs are never mutated and the result shares
// no node with the input. A native TreeNode input is deep-copied first; that
// copy is charged as O(n) time and O(n) auxiliary space.
function solve(root) {
  if (Array.isArray(root)) return toLevel(rotate(toTree(root)));
  return rotate(cloneTree(root));
}

// Official LeetCode ABI: rotates the caller's TreeNode graph in place and
// returns the new root (native_effects.mutates_inputs = true). A level-order
// array is converted to fresh nodes first, so array callers see no mutation.
function upsideDownBinaryTree(root) {
  if (Array.isArray(root)) return toLevel(rotate(toTree(root)));
  return rotate(root === undefined ? null : root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.upsideDownBinaryTree = upsideDownBinaryTree;
module.exports.TreeNode = TreeNode;
if (typeof Solution !== "undefined") solve.Solution = Solution;
