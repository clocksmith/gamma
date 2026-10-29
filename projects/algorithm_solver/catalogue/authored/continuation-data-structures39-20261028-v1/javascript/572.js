"use strict";

function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function fromLevelList(arr) {
  if (!arr || arr.length === 0 || arr[0] === null) return null;
  const root = new TreeNode(arr[0]);
  const q = [root];
  let head = 0, i = 1;
  while (head < q.length && i < arr.length) {
    const node = q[head++];
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) {
        node.left = new TreeNode(v);
        q.push(node.left);
      }
    }
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) {
        node.right = new TreeNode(v);
        q.push(node.right);
      }
    }
  }
  return root;
}

function preorderTokens(root) {
  const tokens = [];
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    if (!node) {
      tokens.push("#");
    } else {
      tokens.push("^" + String(node.val));
      stack.push(node.right, node.left);
    }
  }
  return tokens;
}

function solve(root, subRoot) {
  if (Array.isArray(root)) root = fromLevelList(root);
  if (Array.isArray(subRoot)) subRoot = fromLevelList(subRoot);
  const text = preorderTokens(root);
  const pat = preorderTokens(subRoot);
  const m = pat.length;
  const pi = new Array(m).fill(0);
  let j = 0;
  for (let i = 1; i < m; i++) {
    while (j > 0 && pat[i] !== pat[j]) j = pi[j - 1];
    if (pat[i] === pat[j]) j++;
    pi[i] = j;
  }
  j = 0;
  for (let i = 0; i < text.length; i++) {
    const tok = text[i];
    while (j > 0 && tok !== pat[j]) j = pi[j - 1];
    if (tok === pat[j]) {
      j++;
      if (j === m) return true;
    }
  }
  return false;
}

function isSubtree(root, subRoot) {
  return solve(root, subRoot);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isSubtree = isSubtree;
module.exports.TreeNode = TreeNode;
