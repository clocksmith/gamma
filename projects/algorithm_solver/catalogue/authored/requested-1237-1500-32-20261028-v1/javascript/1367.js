"use strict";

function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}

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

function solve(head, root) {
  let pat;
  if (Array.isArray(head)) {
    pat = head.slice();
  } else {
    pat = [];
    let cur = head;
    while (cur !== null && cur !== undefined) {
      pat.push(cur.val);
      cur = cur.next;
    }
  }
  if (Array.isArray(root)) root = fromLevel(root);
  const m = pat.length;
  const pi = new Int32Array(m);
  let j = 0;
  for (let i = 1; i < m; i++) {
    while (j > 0 && pat[i] !== pat[j]) j = pi[j - 1];
    if (pat[i] === pat[j]) j++;
    pi[i] = j;
  }
  const stack = [[root, 0]];
  while (stack.length > 0) {
    let [node, k] = stack.pop();
    if (!node) continue;
    while (k > 0 && node.val !== pat[k]) k = pi[k - 1];
    if (node.val === pat[k]) {
      k++;
      if (k === m) return true;
    }
    stack.push([node.left, k], [node.right, k]);
  }
  return false;
}

function isSubPath(head, root) {
  return solve(head, root);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isSubPath = isSubPath;
module.exports.ListNode = ListNode;
module.exports.TreeNode = TreeNode;
